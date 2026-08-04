# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
from __future__ import annotations

import json
import logging
import os
import pickle
import random
import tempfile
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from enum import IntEnum
from pathlib import Path

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
from telebot.types import KeyboardButton
from telebot.types import ReplyKeyboardMarkup
from telegram_bot_calendar import LSTEP
from telegram_bot_calendar import DetailedTelegramCalendar

from leistungsbot import leistungs_calendar
from leistungsbot import leistungs_config as lc
from leistungsbot.google_place import Places
from leistungsbot.leistungs_db import LeistungsDB
from leistungsbot.leistungs_returns import LeistungsReturnCodes

#: How long an unread scratch file is kept before `sweep_rand_files` takes
#: it. Days rather than hours: the id sits in an inline button, and nothing
#: stops somebody from scrolling up and pressing it next week.
SCRATCH_MAX_AGE = timedelta(days=7)


class LeistungsTyp(IntEnum):
    NORMAL = 1
    KONKURENZ = 2
    ZUSATZ = 3


class Helper:
    def __init__(self, bot: telebot.TeleBot) -> None:
        self.bot = bot
        self.db = LeistungsDB()
        self.temp_dir = tempfile.gettempdir()
        self.google = Places()
        self.dateformat = "%d.%m.%Y"
        #: `None` unless a calendar is configured. Subscribed rather than
        #: called: a leistungstag is closed from a handler, from a button
        #: and from the scheduler, and the table is the one place all three
        #: pass through. See `leistungsbot.leistungs_calendar`.
        self.calendar = leistungs_calendar.from_config(self.db)
        if self.calendar:
            self.db.subscribe(self.calendar.on_change)

    def filter(self):
        """! The predicate that picks out this bot's own inline buttons

        Every keyboard the bot builds carries `{"🍻cmd": value}` as its
        callback data, and `CallbackHandlers.callback_query` is written for
        exactly that shape.

        The `return` at the end used to be missing, so this evaluated to
        `None`. Telebot strips a `None` filter, which left the handler
        registered with no filter at all - it was the catch-all for every
        callback the calendar handler above it did not take, and its "Hi
        Devs!! Handle this callback" branch could never be reached by
        anything but our own json. See #82.
        """

        def inn(callback):
            try:
                data = json.loads(callback.data)
                cmd = [*data][0]
                return cmd.startswith("🍻")
            except BaseException:
                return False

        return inn

    def escape_markdown(self, text: str, markdown_version: int = 2):
        return telebot.formatting.escape_markdown(text)

    def get_full_temp_file(self, file_id: str):
        return os.path.join(self.temp_dir, str(file_id) + "_leistung")

    def get_full_temp_file_handle(self, file_id: str, rw=False):
        path = self.get_full_temp_file(file_id)
        if rw:
            return open(path, "wb")
        else:
            return open(path, "rb")

    def store_to_rand_file(self, data):
        """! Pickles `data` and hands back the id an inline button carries

        Whoever asks for one of these owns it. `load_from_rand_file` is the
        happy path, `discard_rand_file` is the abandoned one, and the id
        belongs in the presser's `UserContext` in the meantime so
        `process_cancel` can find it. See #97.
        """
        rand_id = random.randint(10000, 100000)
        with self.get_full_temp_file_handle(rand_id, True) as handle:
            pickle.dump(data, handle)
        return rand_id

    def peak_from_rand_file(self, rand_id):
        with self.get_full_temp_file_handle(rand_id) as handle:
            return pickle.load(handle)

    def load_from_rand_file(self, rand_id):
        with self.get_full_temp_file_handle(rand_id) as handle:
            data = pickle.load(handle)
        os.remove(self.get_full_temp_file(rand_id))
        return data

    def discard_rand_file(self, rand_id) -> bool:
        """! Throws away a scratch file without reading it

        For the paths that end a workflow instead of finishing it.

        @returns Whether there was still a file to delete
        """
        try:
            os.remove(self.get_full_temp_file(rand_id))
            return True
        except FileNotFoundError:
            return False

    def sweep_rand_files(self, max_age: timedelta = SCRATCH_MAX_AGE) -> int:
        """! Deletes scratch files that nobody is going to come back for

        The cancel paths cover the user who says no. This covers the one who
        simply stops: no message ever arrives, so nothing else notices. The
        deadline is generous because an inline button stays pressable for as
        long as its message exists.

        @param max_age How long a scratch file may sit unread
        @returns How many files were deleted
        """
        deadline = datetime.now() - max_age
        deleted = 0
        try:
            entries = list(Path(self.temp_dir).glob("*_leistung"))
        except OSError:
            logging.warning("could not read %s", self.temp_dir, exc_info=True)
            return 0
        for path in entries:
            try:
                if datetime.fromtimestamp(path.stat().st_mtime) > deadline:
                    continue
                path.unlink()
                deleted += 1
            except OSError:
                # somebody else's file, or it went away underneath us
                logging.debug("could not sweep %s", path, exc_info=True)
        return deleted

    def location_keyboard(self):
        markup = ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
        for location in self.db.getVirgineLocations():
            markup.add(KeyboardButton(location[0]))
        return markup

    def rating_keyboard(self):
        markup = ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
        # hack to allow for .25 rating
        for i in range(0, 600, 25):
            markup.add(KeyboardButton(self.get_stars(i / 100)))
            if i == 500:
                return markup
        return markup

    def virgine_location_button(self):
        markup = InlineKeyboardMarkup(row_width=1)
        for location in self.db.getVirgineLocations():
            markup.add(
                InlineKeyboardButton(
                    location[0],
                    callback_data=json.dumps({"🍻location": location[1]}),
                ),
            )
        return markup

    def polls_button(self, leistungstage, additional_button=False):
        markup = InlineKeyboardMarkup(row_width=1)
        if leistungstage:
            for leistungstag in leistungstage:
                callback_key = (
                    "🍻closed" if leistungstag["closed"] == 1 else "🍻open"
                )
                markup.add(
                    InlineKeyboardButton(
                        self.db.getLocationName(leistungstag["location"]),
                        callback_data=json.dumps(
                            {callback_key: leistungstag["key"]},
                        ),
                    ),
                )
        if additional_button:
            markup.add(
                InlineKeyboardButton(
                    "Nö",
                    callback_data=json.dumps({"🍻no": None}),
                ),
            )
        return markup

    def open_polls_button(self, additional_button=False):
        leistungstage = self.db.getOpenLeistungsTag()
        return self.polls_button(leistungstage, additional_button)

    def confirm_leistungstag_button(self, leistungstag_key):
        """Use for sendreminder or closepoll"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                "Na",
                callback_data=json.dumps({"🍻cancel": None}),
            ),
            InlineKeyboardButton(
                "Jo",
                callback_data=json.dumps(
                    {"🍻open": leistungstag_key},
                ),
            ),
        )
        return markup

    def check_open_hours_keyboard(
        self,
        agree_message,
        abort_message="Hoitaus. Abort!",
    ):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(
                agree_message,
                callback_data=json.dumps({"🍻open_hours_checked": True}),
            ),
        )
        markup.add(
            InlineKeyboardButton(
                abort_message,
                callback_data=json.dumps({"🍻open_hours_checked": False}),
            ),
        )
        return markup

    def search_location(self, query):
        g_places = self.google.findPlace(query)
        return len(g_places), self.store_to_rand_file(g_places)

    def search_location_button(self, rand_id):
        g_places = self.peak_from_rand_file(rand_id)
        markup = InlineKeyboardMarkup(row_width=1)
        for i in range(len(g_places)):
            markup.add(
                InlineKeyboardButton(
                    f"""{g_places[i]['name']} - {
                        g_places[i]
                        ['formatted_address']
                    }""",
                    callback_data=json.dumps({"🍻search": (rand_id, i)}),
                ),
            )
        return markup

    def restore_search_location_button(self, rand_id):
        markup = InlineKeyboardMarkup(row_width=1)
        g = self.peak_from_rand_file(rand_id)
        for i in range(len(g)):
            markup.add(
                InlineKeyboardButton(
                    g[i]["name"],
                    callback_data=json.dumps({"🍻search": (rand_id, i)}),
                ),
            )
        return markup

    def approve_location_button(self, rand_id, index):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(
                "Ned mei location",
                callback_data=json.dumps({"🍻select": (rand_id, -1)}),
            ),
            InlineKeyboardButton(
                "Des is mei location",
                callback_data=json.dumps(
                    {"🍻select": (rand_id, index)},
                ),
            ),
        )
        return markup

    def leistungstag_type_button(self, key: str):
        markup = InlineKeyboardMarkup(row_width=1)
        for i in LeistungsTyp:
            markup.add(
                InlineKeyboardButton(
                    i.name,
                    callback_data=json.dumps({key: i}),
                ),
            )
        return markup

    def leistungstag_poll_type_button(self):
        return self.leistungstag_type_button("🍻poll_type")

    def leistungstag_history_type_button(self):
        return self.leistungstag_type_button("🍻history_type")

    def leistungstag_purge_type_button(self):
        return self.leistungstag_type_button("🍻purge_type")

    def leistungstag_button(self, key: str, type: int, limit: int = 100):
        history = self.db.getHistory(type, limit)
        markup = InlineKeyboardMarkup(row_width=1)
        for i in range(len(history)):
            name = (
                str(i + 1)
                + "."
                + str(self.db.getLocationName(history[i]["location"]))
            )
            markup.add(
                InlineKeyboardButton(
                    name,
                    callback_data=json.dumps({key: history[i]["key"]}),
                ),
            )
        return markup

    def leistungstag_history_button(self, type):
        return self.leistungstag_button("🍻history", type)

    def leistungstag_dry_purge_button(self, type):
        return self.leistungstag_button("🍻dry_purge", type, 5)

    def leistungstag_purge_button(self, key):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                "Des mochn ma ned!",
                callback_data=json.dumps({"🍻cancel": None}),
            ),
            InlineKeyboardButton(
                "Weg damit",
                callback_data=json.dumps(
                    {"🍻purge": key},
                ),
            ),
        )
        return markup

    def unkown_location_button(self, location):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                "Na",
                callback_data=json.dumps({"🍻cancel": None}),
            ),
            InlineKeyboardButton(
                "Jo",
                callback_data=json.dumps(
                    {"🍻q": location},
                ),
            ),
        )
        return markup

    def dry_run_button(self, rand_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                "Na",
                callback_data=json.dumps({"🍻cancel": None}),
            ),
            InlineKeyboardButton(
                "Jo",
                callback_data=json.dumps(
                    {"🍻publish": rand_id},
                ),
            ),
        )
        return markup

    def user_has_permission(self, user_id: int) -> bool:
        """! Whether `user_id` is an administrator of the leistungschat

        Takes the id rather than a message, because the person to check is
        not always the author of one. An inline button sits on a message the
        bot itself sent, so a callback has to pass `call.from_user.id` - see
        `sender_has_permission` and #99.
        """
        member = self.bot.get_chat_member(
            lc.config["leistungschat_id"],
            user_id,
        )
        return member.status == "administrator" or member.status == "creator"

    def sender_has_permission(self, msg):
        """! Whether the author of `msg` may run an admin command

        Only for messages a *person* sent. Do not pass the message an inline
        keyboard sits on: that one was sent by the bot, so this would ask
        whether the bot is an administrator - which it is, it has to pin and
        stop polls, and the answer would be yes for everybody (#99). Use
        `user_has_permission(call.from_user.id)` there.
        """
        return self.user_has_permission(msg.from_user.id)

    def send_nude(self, chat_id):
        gif = f"https://cdn.porngifs.com/img/{random.randint(1, 39239)}"
        self.bot.send_animation(
            chat_id,
            gif,
            caption="brought to you by Maxmaier",
            has_spoiler=True,
        )

    def next_leistungstag(self):
        return datetime.now() + timedelta(
            days=(8 - datetime.now().weekday()),
        )

    def send_leistungstag(
        self,
        chat_id,
        location: str,
        type: LeistungsTyp = LeistungsTyp.NORMAL,
        date: datetime = None,
        dry_run: bool = True,
    ):
        """! Sends the venue and the poll for a leistungstag

        @returns On a dry run the id of the scratch file holding the
                 preview, so the caller can clean it up. `None` otherwise.
        """
        if not date:
            date = self.next_leistungstag()
        date_str = date.strftime(self.dateformat)
        # close_date = date - timedelta(hours=12)
        info = self.db.getLocationInfo(location)
        venue_id = self.bot.send_venue(
            chat_id,
            latitude=info["lat"],
            longitude=info["lng"],
            title=info["name"],
            address=info["address"],
        )
        count = self.db.getHistoryCount(type)
        count = count + 1 if count else 1
        if type == LeistungsTyp.NORMAL:
            question = f'Leistungstag {count}: am {date_str} in "{location}"'
        elif type == LeistungsTyp.KONKURENZ:
            question = f'Konkurrenz Leistungstag {count}: am {date_str} in "{location}"'
        elif type == LeistungsTyp.ZUSATZ:
            question = f'Leistungstag Zusatztermin {count}: am {date_str} in "{location}"'
        else:
            question = "Keine Ahnung wos wia grad polln..."
        poll_message = self.bot.send_poll(
            chat_id,
            question,
            ["Bin dabei", "Keine Zeit"],
            allows_multiple_answers=False,
            explanation="Soi i da jez a nu erklährn wie ma obstimmt?",
            is_anonymous=False,
        )
        if dry_run:
            rand_id = self.store_to_rand_file((location, type, date))
            self.bot.send_message(
                chat_id,
                "Woin ma des so veröffentlichen?",
                reply_markup=self.dry_run_button(rand_id),
            )
            # handed back so the caller - which knows who pressed the
            # button - can put it in their context and clean it up if the
            # preview is rejected. See #97.
            return rand_id
        else:
            self.db.addLeistungsTag(
                date,
                location,
                poll_message.message_id,
                venue_id.message_id,
                int(type),
            )
            self.db.setLocationVisitedState(location, True)
            self.bot.pin_chat_message(chat_id, poll_message.message_id)

    def send_location_info(self, chat_id, place_id, reply_markup=None):
        info = self.google.getPlaceInfo(place_id)
        self.bot.send_venue(
            chat_id,
            info["geometry"]["location"]["lat"],
            info["geometry"]["location"]["lng"],
            info["name"],
            info["formatted_address"],
            google_place_id=place_id,
            reply_markup=reply_markup,
        )

    def approve_location(self, chat_id, rand_id, index):
        data = self.peak_from_rand_file(rand_id)
        self.send_location_info(
            chat_id,
            data[index]["place_id"],
            self.approve_location_button(rand_id, index),
        )

    def add_location(self, rand_id, index) -> LeistungsReturnCodes:
        data = self.load_from_rand_file(rand_id)
        return self.db.addLocation(
            data[index]["place_id"],
            data[index]["name"],
        )

    def backup_filename(self, now: datetime = None) -> str:
        now = now if now else datetime.now()
        return f"leistungsbot-backup-{now.strftime('%Y%m%d-%H%M%S')}.sqlite"

    def send_backup(self, chat_id) -> str:
        """! Sends a copy of the database as a document

        A snapshot rather than a SQL dump: it is taken with `VACUUM INTO`,
        so it is consistent even while the bot keeps working, and it can be
        opened directly instead of having to be replayed.

        @param chat_id Chat that gets the backup

        @returns The name the backup was sent under
        """
        name = self.backup_filename()
        path = Path(self.temp_dir) / name
        self.db.snapshot(path)
        try:
            with open(path, "rb") as handle:
                self.bot.send_document(
                    chat_id,
                    handle,
                    visible_file_name=name,
                    caption="Do host dei Backup. Pass guat drauf auf!",
                    disable_notification=True,
                )
        finally:
            # missing_ok, so a failed snapshot reports its own error rather
            # than being replaced by a FileNotFoundError from the cleanup
            path.unlink(missing_ok=True)
        return name

    def remove_location(self, locationname):
        key = self.db.getLocationKey(locationname)
        self.db.removeLocation(key)

    def publish_leistungstag(self, rand_id):
        vals = self.load_from_rand_file(rand_id)
        self.send_leistungstag(
            lc.config["leistungschat_id"],
            vals[0],
            vals[1],
            vals[2],
            False,
        )

    def get_rand_len(self, rand_id):
        return len(self.peak_from_rand_file(rand_id))

    def get_stars(self, rating: float):
        if rating > 5:
            rating = 5
        res = "🌕" * int(rating)
        rating -= int(rating)
        if rating >= 0.625:
            res += "🌖"
        elif rating >= 0.325:
            res += "🌗"
        elif rating > 0:
            res += "🌘"
        return res.ljust(5, "🌑")

    def get_rating(self, rating: str):
        return (
            rating.count("🌕")
            + rating.count("🌖") * 0.75
            + rating.count("🌗") * 0.5
            + rating.count("🌘") * 0.25
        )

    def send_history_info(self, chat_id, leistungstag_key: int):
        ld = self.db.getLeistungstag(leistungstag_key)
        info = self.db.getLocationInfoByKey(ld["location"])
        rating = self.db.getAvgLocationRating(info["name"])

        message = (
            f"""*{self.escape_markdown(info.get('name'))}*"""
            + self.escape_markdown(
                f"""
{ld['date'].strftime(self.dateformat)}
{self.get_stars(rating)}
{info.get('address')}
{info.get('phone')}
{info.get('url')}""",
            )
        )

        self.bot.send_message(
            chat_id,
            message,
            parse_mode="MarkdownV2",
        )

    def send_location_info2(self, chat_id, location_key: int):
        info = self.db.getLocationInfoByKey(location_key)
        self.send_location_info(chat_id, info["google-place-id"])

        message = (
            f"""*{self.escape_markdown(info.get('name'))}*"""
            + self.escape_markdown(
                f"""
{info.get('address')}
{info.get('phone')}
{info.get('url')}""",
            )
        )
        self.bot.send_message(
            chat_id,
            message,
            parse_mode="MarkdownV2",
        )

    def send_purge_info(self, chat_id, leistungstag_key: int):
        ld = self.db.getLeistungstag(leistungstag_key)
        info = self.db.getLocationInfoByKey(ld["location"])
        rating = self.db.getAvgLocationRating(info["name"])

        message = (
            f"""*{self.escape_markdown(info.get('name'))}*"""
            + self.escape_markdown(
                f"""
{ld['date'].strftime(self.dateformat)}
{self.get_stars(rating)}
{info.get('address')}
{info.get('phone')}
{info.get('url')}""",
            )
        )

        self.bot.send_message(
            chat_id,
            message,
            parse_mode="MarkdownV2",
            reply_markup=self.leistungstag_purge_button(leistungstag_key),
        )

    def purge_leistungstag(self, leistungstag_key: int):
        ld = self.db.getLeistungstag(leistungstag_key)
        res = False
        try:
            res = self.bot.delete_message(
                lc.config["leistungschat_id"],
                ld["poll_id"],
            )
        except BaseException:
            pass
        try:
            res &= self.bot.delete_message(
                lc.config["leistungschat_id"],
                ld["venue_id"],
            )
        except BaseException:
            pass
        self.db.setLocationVisitedStateKey(ld["location"], False)
        self.db.removeLeistungstag(leistungstag_key)
        return res

    def migrated_chat_id(self, error) -> int | None:
        """! The new chat id after a group was upgraded to a supergroup

        Telegram answers every request to the old id with a 400 and hands the
        replacement id back in `parameters.migrate_to_chat_id`.

        @returns The new chat id, or None if this is not a migration error
        """
        if not isinstance(error, ApiTelegramException):
            return None
        parameters = (error.result_json or {}).get("parameters", {})
        return parameters.get("migrate_to_chat_id")

    def report_error(self, message, error) -> None:
        """! Reports a failed command to the user and to the dev chat

        Never raises. The reporter used to be inlined in every handler, so
        when it failed - a stale chat id in the configuration is enough - its
        own exception replaced the one it was meant to report, and the
        original cause was lost.

        @param message Message that triggered the failing command
        @param error The exception that was caught
        """
        logging.exception("command failed: %s", getattr(message, "text", None))

        hint = ""
        migrated = self.migrated_chat_id(error)
        if migrated:
            hint = (
                f"\n\nDe Gruppn is a Supergruppe worden. "
                f"Neue chat id: {migrated}\n"
                f"De Konfiguration muas ogepasst wern, "
                f"sunst geht goa nix mehr."
            )

        try:
            self.bot.reply_to(message, f"An error occurred!\nError: {error}")
        except Exception:
            logging.exception("could not tell the user about the error")

        details = (
            f"Hi Devs!!\nHandle This Error plox\n{error}\n\n"
            f"Command: {getattr(message, 'text', None)}\n"
            f"User: {getattr(message, 'from_user', None)}\n"
            f"Chat: {getattr(getattr(message, 'chat', None), 'id', None)}"
            f"{hint}"
        )
        try:
            self.bot.send_message(lc.config["chat_id"], details)
        except Exception:
            logging.exception("could not tell the devs about the error")

    def pick_date(self, chat_id):
        calendar, step = DetailedTelegramCalendar(
            min_date=date.today(),
        ).build()
        self.bot.send_message(
            chat_id,
            f"Select {LSTEP[step]}",
            reply_markup=calendar,
        )

    def date_suggester(self):
        markup = InlineKeyboardMarkup(row_width=1)
        next_tuseday = self.next_leistungstag()
        markup.add(
            InlineKeyboardButton(
                next_tuseday.strftime(self.dateformat),
                callback_data=json.dumps(
                    {"🍻poll_date": next_tuseday.strftime(self.dateformat)},
                ),
            ),
        )
        markup.add(
            InlineKeyboardButton(
                "Anderes Datum",
                callback_data=json.dumps({"🍻poll_date": None}),
            ),
        )
        return markup

    def check_open_hours(
        self,
        location: str,
        date: date,
        time: time = time(19, 00),
    ):
        place_info = self.db.getLocationInfo(location)
        return self.google.checkOpenHours(
            place_info["google-place-id"],
            date,
            time,
        )


class PersistantLeistungsTagPoller:
    def __init__(
        self,
        helper: Helper,
        chat_id,
        location: str,
        type: LeistungsTyp = LeistungsTyp.NORMAL,
        date: datetime = None,
    ):
        self.chat_id = chat_id
        self.location = location
        self.type = type
        self.date = date if date else helper.next_leistungstag()
        self.helper = helper

    def dry_send_with_date(self, date: datetime):
        """! @returns The scratch file id behind the preview's buttons"""
        return self.helper.send_leistungstag(
            self.chat_id,
            self.location,
            self.type,
            date,
            True,
        )

    def dry_send(self):
        """! @returns The scratch file id behind the preview's buttons"""
        return self.helper.send_leistungstag(
            self.chat_id,
            self.location,
            self.type,
            self.date,
            True,
        )
