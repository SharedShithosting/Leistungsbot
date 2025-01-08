# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
from __future__ import annotations

import argparse
import importlib.resources
import json
import logging
import time
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import telebot
from telebot import custom_filters
from telebot.handler_backends import State
from telebot.handler_backends import StatesGroup
from telebot.storage import StateMemoryStorage
from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_calendar import LSTEP

from leistungsbot import leistungs_config as lc
from leistungsbot.BotHelper import Helper
from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.BotHelper import PersistantLeistungsTagPoller
from leistungsbot.BotScheduler import Scheduler
from leistungsbot.google_place import Openness
from leistungsbot.leistungs_returns import LeistungsReturnCodes
from leistungsbot.package import _version

# States storage
# Now, you can pass storage to bot.
state_storage = StateMemoryStorage()  # you can init here another storage

#      ┌──────────────────────────────────────────────────────────┐
#      │                        HELP TEXT                         │
#      └──────────────────────────────────────────────────────────┘
"""
User Available Commands:
    1.  /leistungspoll
    2.  /add_location
    3.  /help
    4.  /purge
    5.  /mario
    6.  /start
    7.  /sendnudes
    8.  /rate_location
    9.  /show_participants
    10. /reminde_me
    11. /show_locations
    12. /remove_location
    13. /location_info
    14. /zusatzpoll
    15. /konkurrenzpoll
    16. /version

Developer Commands: #NOTE: ONLY @eckphi is
 allowed for these comands:
    1. /showIds
    2. /botlogs
"""

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.

# ──────────────────────────────────── States Group ──────────────────────


class LeistungsState(StatesGroup):
    # Just name variables differently
    normalLocation = (
        State()
    )  # creating instances of State class is enough from now
    konkurrenzLocation = State()
    zusatzLocation = State()
    searchLocation = State()
    purgeLeistungstag = State()
    historyLeistungstag = State()
    remindePoll = State()
    closePoll = State()
    sneakyClosePoll = State()
    removeLocation = State()
    rateLocation = State()
    genericLeistungsmessage = State()
    switcherooLeistungstagNumber = State()
    switcherooAlternateLocation = State()


class UserContext(TypedDict):
    leistungstag: dict | None


class LeistungsBot:
    def __init__(self) -> None:
        self.bot = bot = telebot.TeleBot(lc.config["bot_token"])
        self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))
        self.helper = Helper(self.bot)
        self.scheduler = Scheduler(self.bot)
        self.poller = None
        self.last_text_nudes = datetime.min
        self.user_context: dict[int, UserContext] = {}

        @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
        def cal(call):
            result, key, step = DetailedTelegramCalendar(
                min_date=date.today(),
            ).process(call.data)
            if not result and key:
                self.helper.bot.edit_message_text(
                    f"Select {LSTEP[step]}",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=key,
                )
            elif result:
                self.helper.bot.edit_message_text(
                    f"You selected {result}",
                    call.message.chat.id,
                    call.message.message_id,
                )
                if not self.poller:
                    self.helper.bot.send_message(
                        call.message.chat_id,
                        "Da is wohl was schiefglaufen, i kann ka poll findn...",
                    )
                    return
                if (
                    self.poller.type == LeistungsTyp.NORMAL
                    or self.poller.type == LeistungsTyp.KONKURENZ
                ) and result.weekday() != 1:
                    self.helper.bot.send_message(
                        call.message.chat.id,
                        "Blasphemie, des is ka Dienstag wast da du do ausgsuacht hast...alles auf eigene Gefahr!",
                    )
                    time.sleep(1)

                self.check_open_hours_before_sending(call, result)

        @bot.callback_query_handler(func=self.helper.filter())
        def callback_query(call):
            try:
                data = json.loads(call.data)
                if len(data) == 0:
                    bot.answer_callback_query(
                        call.id,
                        "SHHEEEEESH des hod ned funktioniert",
                    )
                    return
                cmd = [*data][0].replace("🍻", "")
                val = [*data.values()][0]
                bot.answer_callback_query(call.id, "Copy that")
                if cmd == "search":
                    self.helper.approve_location(
                        call.message.chat.id,
                        val[0],
                        val[1],
                    )
                elif cmd == "select":
                    if val[1] < 0:
                        if (self.helper.get_rand_len(val[0])) == 1:
                            self.bot.send_message(
                                call.message.chat.id,
                                "Daun füg a boa mehr infos zu deiner Suche dazua...",
                            )
                        else:
                            self.bot.send_message(
                                call.message.chat.id,
                                "Daun probiern mas numoi...",
                                reply_markup=self.helper.restore_search_location_button(
                                    val[0],
                                ),
                            )
                    else:
                        res = self.helper.add_location(val[0], val[1])
                        if res == LeistungsReturnCodes.DB_DUPLICATE:
                            self.bot.send_message(
                                call.message.chat.id,
                                "Des isch scho drin, du deppata!",
                            )
                elif cmd == "cancle":
                    self.process_cancle(call.message)
                elif cmd == "publish":
                    self.helper.publish_leistungstag(val)
                    bot.send_message(
                        call.message.chat.id,
                        "Hauma so veröffentlicht",
                    )
                elif cmd == "q":
                    self.process_search_location(call.message.chat.id, val)
                elif cmd == "history_type":
                    self.bot.send_message(
                        call.message.chat.id,
                        "Welchen Leistungstag willst da anschaun?",
                        reply_markup=self.helper.leistungstag_history_button(
                            LeistungsTyp(val),
                        ),
                    )
                elif cmd == "purge_type":
                    self.bot.send_message(
                        call.message.chat.id,
                        "Welchen Leistungstag willst löschen?",
                        reply_markup=self.helper.leistungstag_dry_purge_button(
                            LeistungsTyp(val),
                        ),
                    )
                elif cmd == "history":
                    self.helper.send_history_info(
                        call.message.chat.id,
                        val,
                    )
                elif cmd == "dry_purge":
                    self.helper.send_purge_info(
                        call.message.chat.id,
                        val,
                    )
                elif cmd == "purge":
                    if self.helper.purge_leistungstag(val):
                        bot.send_message(
                            call.message.chat.id,
                            "zack und weg ises",
                        )
                    else:
                        bot.send_message(
                            call.message.chat.id,
                            "De Nachrichtn muast leida manuell löschen",
                        )
                elif cmd == "location":
                    self.helper.send_location_info2(call.message.chat.id, val)
                elif cmd == "open":
                    if (
                        self.bot.get_state(
                            call.from_user.id,
                            call.message.chat.id,
                        )
                        == LeistungsState.remindePoll.name
                    ):
                        self.process_reminder(call.message, val)
                    elif (
                        self.bot.get_state(
                            call.from_user.id,
                            call.message.chat.id,
                        )
                        == LeistungsState.closePoll.name
                    ):
                        self.process_closepoll(call.message, val)
                    elif (
                        self.bot.get_state(
                            call.from_user.id,
                            call.message.chat.id,
                        )
                        == LeistungsState.sneakyClosePoll.name
                    ):
                        self.process_closepoll(call.message, val, True)
                    elif (
                        self.bot.get_state(
                            call.from_user.id,
                            call.message.chat.id,
                        )
                        == LeistungsState.genericLeistungsmessage.name
                    ):
                        self.process_generic_leistungsmessage(
                            call.message.reply_to_message,
                            val,
                        )
                elif cmd == "closed":
                    self.bot.reply_to(
                        call.message,
                        "Der Poll is scho closed. Willst wirklich on den reminden?",
                        reply_markup=self.helper.confirm_leistungstag_button(
                            val,
                        ),
                    )
                elif cmd == "no":
                    self.process_generic_leistungsmessage(
                        call.message.reply_to_message,
                        val,
                    )
                elif cmd == "poll_date":
                    if val:
                        if not self.poller:
                            self.helper.bot.send_message(
                                call.message.chat_id,
                                "Da is wohl was schiefglaufen, i kann ka poll findn...",
                            )
                        else:
                            self.check_open_hours_before_sending(
                                call,
                                datetime.strptime(
                                    val,
                                    self.helper.dateformat,
                                ).date(),
                            )
                    else:
                        self.helper.pick_date(call.message.chat.id)
                elif cmd == "open_hours_checked":
                    self.process_check_open_hours(call, val)
                else:
                    bot.send_message(
                        lc.config["chat_id"],
                        f"Hi Devs!!\nHandle this callback\n{cmd}",
                    )
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(
                    call.message,
                    f"An error occurred!\nError: {error}",
                )
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["showIds"])
        def showIds(message):
            try:
                if message.from_user.username in lc.config["usernames"]:
                    file = open("joined_groups.txt", "r ")
                    bot.send_document(message.chat.id, file)
                    file.close()

            except Exception as error:
                bot.send_message(lc.config["chat_id"], str(error))

        @bot.message_handler(commands=["stats", "groups"])
        def stats(message):
            try:
                if message.from_user.username in lc.config["usernames"]:
                    print("Sending Stats To Owner")
                    with open("joined_groups.txt") as file:
                        group_ids = []
                        for line in file.readlines():
                            for group_id in line.split(" "):
                                group_ids.append(group_id)
                                no_of_polls = len(group_ids)
                                no_of_groups = len(list(set(group_ids)))
                        group_ids.clear()
                        bot.reply_to(
                            message,
                            f"Number of polls Made: {no_of_polls}\n#Nr of groups bot has been added to: {no_of_groups}",
                        )
                        file.close()
                else:
                    bot.reply_to(
                        message,
                        f"Sorry {message.from_user.username}! You Are Not Allowed To Use This Command,",
                    )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                try:
                    group_ids.clear()
                except BaseException:
                    pass
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["botlogs"])
        def ViewTheLogsFile(message):
            try:
                if message.from_user.username in lc.config["usernames"]:
                    print("Owner Asked For The Logs!")
                    file = open("POLL_LOGS.txt")
                    bot.send_document(
                        message.chat.id,
                        file,
                        timeout=60,
                        disable_notification=True,
                    )
                    file.close()
                    print("Logs Sent To Owner")
                else:
                    bot.reply_to(
                        message,
                        f"Sorry {message.from_user.username}! You Are Not Allowed For This Command.",
                    )
            except Exception as error:
                bot.reply_to(message, f"Error: {error}")

        @bot.message_handler(commands=["help"])
        def helper(message):
            return bot.reply_to(message, "Eiso i hüf da do ned...")

        @bot.message_handler(commands=["purge"])
        def purge(message):
            if not self.helper.sender_has_permission(message):
                bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return
            try:
                self.process_purge(message)
            except IndexError:
                return bot.reply_to(
                    message,
                    f"""Lol!!! An error in the wild:
                    {message.text}

                    Which is invalid.
                    For more help use: /help
                    """,
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"""Error From Poll Bot!

                    Error  :: {error}

                    --------------------------------

                    Command:: {message.text}

                    --------------------------------

                    UserDetails: {message.from_user}

                    --------------------------------

                    Date   :: {message.date}

                    --------------------------------

                    The Complete Detail:
                    {message}


                    """,
                )

                return bot.reply_to(
                    message,
                    f"""An Unexpected Error Occured!
                    Error::  {error}
                    The error was informed to @eckphi""",
                )

        @bot.message_handler(commands=["alive"])
        def alive(message):
            bot.reply_to(
                message,
                f"Hey {message.from_user.username}, Ready To Serve You in version {_version.__version__}",
            )

        @bot.message_handler(commands=["start"])
        def start(message):
            bot.reply_to(
                message,
                f"Heya {message.from_user.username}, I am there to help you in polls. But this cmd is bit old try /help.",
            )

        @bot.message_handler(commands=["leistungspoll"])
        def poll_now(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.normalLocation,
                    message.chat.id,
                )
                self.bot.send_message(
                    message.chat.id,
                    "Schick de nexte location muaz",
                    reply_markup=self.helper.location_keyboard(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["zusatzpoll"])
        def zusatz_poll(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.zusatzLocation,
                    message.chat.id,
                )
                self.bot.send_message(
                    message.chat.id,
                    "Schick de nexte location muaz",
                    reply_markup=self.helper.location_keyboard(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["konkurrenzpoll"])
        def konkurrenz_poll(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.konkurrenzLocation,
                    message.chat.id,
                )
                self.bot.send_message(
                    message.chat.id,
                    "Schick de nexte location muaz",
                    reply_markup=self.helper.location_keyboard(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["sendreminder"])
        def send_reminder(message: telebot.types.Message):
            try:
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.remindePoll,
                    message.chat.id,
                )

                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return

                # print(f'Message: {message.text}')
                command_parts = message.text.strip().split()

                if len(command_parts) == 1:
                    self.bot.reply_to(
                        message,
                        "An welchen Poll wüst reminden?",
                        reply_markup=self.helper.open_polls_button(),
                    )
                    return
                else:
                    target_date_str = command_parts[1]

                    try:
                        target_date = date.fromisoformat(target_date_str)
                    except BaseException:
                        target_date = None
                        self.bot.send_message(
                            message.chat.id,
                            f"Soi des a Datum sei? Schick ma wonn donn sowos wie {datetime.now().date().isoformat()}",
                        )
                        self.bot.reply_to(
                            message,
                            "An welchen Poll wüst reminden?",
                            reply_markup=self.helper.open_polls_button(),
                        )

                    # print(f'Date: {target_date}')

                    if target_date is not None:
                        successful = (
                            self.try_remind_to_leistungstag_on_a_specific_date(
                                message,
                                target_date,
                            )
                        )
                        if not successful:
                            self.bot.reply_to(
                                message,
                                "An welchen Poll wüst reminden?",
                                reply_markup=self.helper.open_polls_button(),
                            )

            except Exception as error:
                self.bot.delete_state(message.from_user.id, message.chat.id)

                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["closepoll"])
        def close_poll(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return

                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.closePoll,
                    message.chat.id,
                )
                self.bot.reply_to(
                    message,
                    "Welchen Poll wüst closen?",
                    reply_markup=self.helper.open_polls_button(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["sneaky_closepoll"])
        def sneaky_close_poll(message: telebot.types.Message) -> None:
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return

                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.sneakyClosePoll,
                    message.chat.id,
                )
                self.bot.reply_to(
                    message,
                    "Welchen Poll wüst sneaky closen?",
                    reply_markup=self.helper.open_polls_button(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["sendnudes"])
        def send_nudes(message):
            try:
                if message.chat.type != "private":
                    bot.reply_to(
                        message,
                        "Bist deppad? Des is nix fürn Gruppen chat, du Drecksau.",
                    )
                else:
                    self.process_send_nudes(message.chat.id)
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["add_location"])
        def add_location(message):
            try:
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.searchLocation,
                    message.chat.id,
                )
                self.bot.send_message(
                    message.chat.id,
                    "Schick dei location idee muaz",
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["remove_location"])
        def remove_location_handler(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return

                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.removeLocation,
                    message.chat.id,
                )
                self.bot.reply_to(
                    message,
                    "Welche Location willst löschen?",
                    reply_markup=self.helper.location_keyboard(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["history"])
        def history(message):
            try:
                self.process_history(message)
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["rate_location"])
        def rate_location_handler(message):
            try:
                if message.chat.type != "private":
                    self.helper.bot.reply_to(
                        message,
                        "Und wenn ma des ned im Gruppenchat machen, du Bauernschädl?",
                    )
                else:
                    leistungstag = self.helper.db.getLeistungsTags(
                        LeistungsTyp.NORMAL,
                        max_results=1,
                        before=datetime.now(),
                    )[0]
                    self.helper.send_location_info2(
                        message.chat.id,
                        leistungstag["location"],
                    )
                    self.helper.bot.send_message(
                        message.chat.id,
                        "Wiafü Monde wüst erm geben?",
                        reply_markup=self.helper.rating_keyboard(),
                    )
                    self.bot.set_state(
                        message.from_user.id,
                        LeistungsState.rateLocation,
                        message.chat.id,
                    )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["show_locations"])
        def show_locations(message):
            try:
                bot.reply_to(
                    message,
                    "Des san de nächsten Locations",
                    reply_markup=self.helper.virgine_location_button(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(commands=["message"])
        def message_handler(message: telebot.types.Message):
            try:
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.remindePoll,
                    message.chat.id,
                )

                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message,
                        "Diese Funktion ist nicht für den Pöbel gedacht.",
                    )
                    return

                # print(f'Message: {message.text}')
                command_parts = message.text.strip().split()
                if len(command_parts) < 2:
                    self.bot.reply_to(
                        message,
                        "Jo, do muast jetzt scho dazuaschreiben wost willst. Probiers numoi",
                    )
                    return

                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.genericLeistungsmessage,
                    message.chat.id,
                )

                self.bot.reply_to(
                    message,
                    "Wüst des auf irgend an poll replyen?",
                    reply_markup=self.helper.open_polls_button(True),
                )

            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state="*", commands=["cancel"])
        def cancel(message):
            try:
                self.process_cancle(message)
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.normalLocation)
        def get_poll_location(message):
            try:
                location = self.process_poll_location(message)
                if location:
                    self.poller = PersistantLeistungsTagPoller(
                        self.helper,
                        message.chat.id,
                        location,
                        LeistungsTyp.NORMAL,
                    )
                    self.helper.bot.reply_to(
                        message,
                        "Für wann wollen ma pollen?",
                        reply_markup=self.helper.date_suggester(),
                    )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.konkurrenzLocation)
        def get_konkurrenz_location(message):
            try:
                location = self.process_poll_location(message)
                if location:
                    self.poller = PersistantLeistungsTagPoller(
                        self.helper,
                        message.chat.id,
                        location,
                        LeistungsTyp.KONKURENZ,
                    )
                    self.helper.bot.reply_to(
                        message,
                        "Für wann wollen ma pollen?",
                        reply_markup=self.helper.date_suggester(),
                    )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.zusatzLocation)
        def get_zusatz_location(message):
            try:
                location = self.process_poll_location(message)
                if location:
                    self.poller = PersistantLeistungsTagPoller(
                        self.helper,
                        message.chat.id,
                        location,
                        LeistungsTyp.ZUSATZ,
                    )
                    self.helper.pick_date(message.chat.id)
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.removeLocation)
        def remove_location(message):
            try:
                self.helper.remove_location(message.text)
                bot.reply_to(message, "Hab de location murz destroyed!")
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error plox\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.searchLocation)
        def search_location(message):
            try:
                self.process_search_location(
                    message.chat.id,
                    message.text.strip(),
                )
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error (LeistungsState.searchLocation)\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.rateLocation)
        def rate_location(message):
            try:
                rating = self.helper.get_rating(message.text)
                leistungstag = self.helper.db.getLeistungsTags(
                    LeistungsTyp.NORMAL,
                    max_results=1,
                    before=datetime.now(),
                )[0]
                self.helper.db.addUser(message.from_user.id, message.chat.id)
                try:
                    self.helper.db.rateLocationKey(
                        leistungstag["location"],
                        message.from_user.id,
                        rating,
                    )
                except BaseException:
                    self.bot.send_message(
                        message.chat.id,
                        "WAHLBETRUG!! Du host schomoi obgstimmt.",
                    )
                self.bot.delete_state(message.from_user.id)
            except Exception as error:
                bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle This Error (LeistungsState.searchLocation)\n{error}",
                )
                bot.reply_to(message, f"An error occurred!\nError: {error}")
                bot.send_message(
                    lc.config["chat_id"],
                    f"An error occurred!\nError: {error}",
                )

        @bot.message_handler(state=LeistungsState.switcherooLeistungstagNumber)
        def switcheroo_leistungstag_number(
            message: telebot.types.Message,
        ) -> None:
            try:
                lt_number = int(message.text)
            except BaseException:
                self.bot.send_message(
                    message.chat.id,
                    "Host du in da Voikschui ned aufpasst wos a nummer is? Probiers numoi ...",
                )

            lt = self.helper.db.getLeistungstagByNumber(lt_number)
            if lt is None:
                self.bot.send_message(
                    message.chat.id,
                    "Den Leistungstog find i ned. Schau numoi genau",
                )
                return

            print(f'Location {lt["location"]}')

            if message.from_user.id not in self.user_context:
                self.user_context[message.from_user.id] = {"leistungstag": lt}
            else:
                self.user_context[message.from_user.id]["leistungstag"] = lt

            self.bot.send_message(
                message.chat.id,
                "Passt. Wo schau ma stottdessen hin?",
                reply_markup=self.helper.location_keyboard(),
            )
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.switcherooAlternateLocation,
                message.chat.id,
            )

        @bot.message_handler(state=LeistungsState.switcherooAlternateLocation)
        def switcheroo_alternate_location(
            message: telebot.types.Message,
        ) -> None:
            if (
                message.from_user.id not in self.user_context
                or "leistungstag"
                not in self.user_context[message.from_user.id]
                or self.user_context[message.from_user.id]["leistungstag"]
                is None
            ):
                self.bot.send_message(
                    message.chat.id,
                    "Could not find Leistungstag in UserContext. This should not happen, please try again ...",
                )
                self.bot.delete_state(message.from_user.id, message.chat.id)
                return

            location = message.text.strip()
            # check if location exists in database
            info = self.helper.db.getLocationInfo(location)

            if not info:
                self.bot.send_message(
                    message.chat.id,
                    f"'{location}' kenn i ned..wüstas stattdessn zur listn dazua gebn?",
                    reply_markup=self.helper.unkown_location_button(location),
                )
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.searchLocation,
                    message.chat.id,
                )

            else:
                lt = self.user_context[message.from_user.id]["leistungstag"]
                self.helper.db.switchLeistungstagLocation(
                    lt["key"],
                    lt["location"],
                    info["key"],
                )

                self.bot.send_message(
                    message.from_user.id,
                    f"Ok, donn gemma am {lt['date'].strftime('%d.%m.%Y')} ins {info['name']}",
                )
                self.bot.delete_state(message.from_user.id, message.chat.id)

            self.user_context[message.from_user.id]["leistungstag"] = None
            # TODO: Edit poll message, if possible

        @bot.message_handler(commands="switcheroo")
        def switcheroo(message: telebot.types.Message) -> None:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )

            self.bot.send_message(
                message.chat.id,
                "Wechan muastn ändern? Schick ma de nummer und i schau wos i doan konn.",
            )
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.switcherooLeistungstagNumber,
                message.chat.id,
            )

        # @bot.message_handler(content_types=["text"])
        # def new_msg(message):
        #     try:
        #         if "nude" in message.text:
        #             if message.chat.type != "private":
        #                 if (datetime.now() - self.last_text_nudes) > timedelta(
        #                     days=1,
        #                 ):
        #                     self.last_text_nudes = datetime.now()
        #                     self.process_send_nudes(message.chat.id)
        #             else:
        #                 self.process_send_nudes(message.chat.id)

        #     except Exception as error:
        #         bot.send_message(
        #             lc.config["chat_id"],
        #             f"Hi Devs!!\nHandle This Error (text)\n{error}",
        #         )
        #         bot.reply_to(message, f"An error occurred!\nError: {error}")

        @bot.message_handler(commands=["version"])
        def version(message):
            bot.reply_to(
                message,
                f"LeistungsBot - {_version.__version__}",
            )

    def process_cancle(self, message):
        self.bot.send_message(
            message.chat.id,
            "Halt Stop.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        self.bot.delete_state(message.from_user.id, message.chat.id)

    def process_poll_location(self, message):
        location = message.text.strip()
        # check if location exists in database
        info = self.helper.db.getLocationInfo(location)
        if not info:
            self.bot.send_message(
                message.chat.id,
                f"'{location}' kenn i ned..wüstas stattdessn zur listn dazua gebn?",
                reply_markup=self.helper.unkown_location_button(location),
            )
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.searchLocation,
                message.chat.id,
            )
        elif info["visited"]:
            self.bot.reply_to(
                message,
                "Do woan ma schomoi, i hoff du wast wost duast.",
            )
            self.bot.delete_state(message.from_user.id, message.chat.id)
            return location
        else:
            self.bot.delete_state(message.from_user.id, message.chat.id)
            return location
        return None

    def process_reminder(self, message, leistungstag_key):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message,
                "Diese Funktion ist nicht für den Pöbel gedacht.",
            )
            return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.bot.send_message(
            lc.config["leistungschat_id"],
            "Reminder. Morgen wird reserviert. Letzte Chance zum Abstimmen 🗳️",
            reply_to_message_id=leistungstag["poll_id"],
        )
        self.bot.send_message(message.chat.id, "Da Reminder is draußen!")

    def process_closepoll(
        self,
        message: telebot.types.Message,
        leistungstag_key: int,
        sneaky: bool = False,
    ) -> None:
        # Check does not work when in callback
        # if not self.helper.sender_has_permission(message):
        #     self.bot.reply_to(
        #         message,
        #         "Diese Funktion ist nicht für den Pöbel gedacht.",
        #     )
        #     return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.helper.db.closeLeistungstag(leistungstag_key)
        try:
            self.bot.stop_poll(
                lc.config["leistungschat_id"],
                leistungstag["poll_id"],
            )
        except BaseException:
            pass
        try:
            self.bot.unpin_chat_message(
                lc.config["leistungschat_id"],
                leistungstag["poll_id"],
            )
        except BaseException:
            pass
        if not sneaky:
            self.bot.send_message(
                lc.config["leistungschat_id"],
                "Schluss, aus, vorbei die Wahl is glaufen und für de de abgstimmt haben is a Platzerl reserviert.",
                reply_to_message_id=leistungstag["poll_id"],
            )
            self.bot.send_message(
                message.chat.id,
                "De Poll is zua. I hoff für dich d Reservierung is scho erledigt!",
            )
        else:
            try:
                sneakiely = (
                    importlib.resources.as_file(
                        importlib.resources.files("resources") / "sneaky.gif",
                    ),
                )
            except BaseException:
                resources = Path(__file__).parent / "resources"
                sneakiely = resources / "sneaky.gif"
            self.bot.send_animation(
                message.chat.id,
                animation=telebot.types.InputFile(
                    sneakiely,
                ),
                caption="De Poll is zua. I hoff für dich d Reservierung is scho erledigt!",
            )

    def process_check_open_hours(self, callback, open_hours_correct):
        if open_hours_correct:
            self.poller.dry_send()

    def process_send_nudes(self, chat_id):
        self.helper.send_nude(chat_id)

    def process_search_location(self, chat_id, query):
        finds, rand_id = self.helper.search_location(query)
        if finds < 1:
            self.bot.send_message(
                chat_id,
                f'Wenn i nach "{query}" suach find i nix...vielleicht verschriebn?',
            )
        elif finds == 1:
            self.helper.approve_location(chat_id, rand_id, 0)
        elif finds > 1:
            self.bot.send_message(
                chat_id,
                "Suach da aus wost willst, oda schick ma wos aunders",
                reply_markup=self.helper.search_location_button(rand_id),
            )

    def process_history(self, message):
        self.bot.send_message(
            message.chat.id,
            "Welche Art von Leistungstag willst da anschaun?",
            reply_markup=self.helper.leistungstag_history_type_button(),
        )

    def process_purge(self, message):
        try:
            responisibility = (
                importlib.resources.as_file(
                    importlib.resources.files("resources")
                    / "responisibility.gif",
                ),
            )
        except BaseException:
            resources = Path(__file__).parent / "resources"
            responisibility = resources / "responisibility.gif"
        self.bot.send_animation(
            message.chat.id,
            telebot.types.InputFile(
                responisibility,
            ),
            caption="Welche Art von Leistungstag willst löschen?",
            reply_markup=self.helper.leistungstag_purge_type_button(),
        )

    def process_generic_leistungsmessage(
        self,
        original_message: telebot.types.Message,
        leistungstag_id,
    ):
        command_parts = original_message.text.strip().split()
        msg = " ".join(command_parts[1:])

        if leistungstag_id is not None:
            leistungstag = self.helper.db.getLeistungstag(leistungstag_id)
            self.bot.send_message(
                lc.config["leistungschat_id"],
                msg,
                reply_to_message_id=leistungstag["poll_id"],
            )
        else:
            self.bot.send_message(lc.config["leistungschat_id"], msg)

        print(
            f'User {original_message.from_user.username} sent generic message "{msg}"',
        )

        self.bot.delete_state(
            original_message.from_user.id,
            original_message.chat.id,
        )

    def check_open_hours_before_sending(self, call, date: date):
        open_state = self.helper.check_open_hours(self.poller.location, date)

        if open_state[0] == Openness.OPEN:
            self.poller.dry_send_with_date(date)
        else:
            self.poller.date = date

            if open_state[0] == Openness.CLOSED:
                self.bot.send_message(
                    call.message.chat.id,
                    "I glaub ned, dass de offn hom. Bist da sicha?\n\n"
                    + open_state[1],
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Des passt so, i kenn mi aus",
                    ),
                )
            elif open_state[0] == Openness.SHORT:
                self.bot.send_message(
                    call.message.chat.id,
                    "Is da des long gmua?\n\n" + open_state[1],
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Jo, passt scho",
                    ),
                )
            elif open_state[0] == Openness.UNKNOWN:
                self.bot.send_message(
                    call.message.chat.id,
                    "I was jetzt hod ned, ob de offen hom. Muast söwa schaun.",
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Des passt so, i kenn mi aus",
                        "Schaut schlecht aus",
                    ),
                )

    def try_remind_to_leistungstag_on_a_specific_date(
        self,
        message: telebot.types.Message,
        target_date: date,
    ) -> bool:
        """! Reminds to polls of leistungstag on a specific date

        @param message Reminder command message
        @param target_date Date of the Leistungstag(e)

        @returns If Leistungstage on this date where found
        """

        if target_date < datetime.now().date():
            self.bot.send_message(
                message.chat.id,
                "Für des is zu spät zum reminden. Suach da wos ondares aus ...",
            )
            return False

        leistungstage = self.helper.db.getLeistungstageByDate(target_date)
        # print(f'Leistungstage: {leistungstage}')

        if leistungstage is None:
            self.bot.send_message(
                message.chat.id,
                "An dem Tog is ka Leistungstog. Suach da wos ondares aus ...",
            )
            return False

        if len(leistungstage) == 1:
            leistunstag = leistungstage[0]
            location_name = self.helper.db.getLocationName(
                leistunstag["location"],
            )

            if leistunstag["closed"] == 1:
                self.bot.reply_to(
                    message,
                    f"Leistungstag an dem Tog is bei {location_name}, aber da Poll is scho geclosed. Willst wirklich on den reminden?",
                    reply_markup=self.helper.confirm_leistungstag_button(
                        leistunstag["key"],
                    ),
                )
            else:
                self.bot.reply_to(
                    message,
                    f"Leistungstag an dem Tog is bei {location_name}. Willst on den reminden?",
                    reply_markup=self.helper.confirm_leistungstag_button(
                        leistunstag["key"],
                    ),
                )

        else:
            self.bot.send_message(
                message.chat.id,
                "Ein wöd Tog. Do san sogor mehrere Leistungstoge!",
            )
            self.bot.reply_to(
                message,
                "An welchen Poll wüst reminden?",
                reply_markup=self.helper.polls_button(leistungstage),
            )

        return True

    def infinite_poll(self):
        self.bot.infinity_polling()

    def poll(self):
        self.bot.polling()


def main():
    parser = argparse.ArgumentParser(
        description="LeistungsBot - some realy weird bot.",
    )
    parser.add_argument(
        "--google",
        "-g",
        dest="google",
        help="Google api key",
    )
    parser.add_argument(
        "--token",
        "-t",
        dest="bot_token",
        help="Telegram bot token generated by @BotFather",
    )
    parser.add_argument(
        "--hash",
        dest="api_hash",
        help="api hash from my.telegram.org",
    )
    parser.add_argument(
        "--id",
        dest="api_id",
        help="api id from my.telegram.org",
    )
    parser.add_argument(
        "--chat",
        dest="chat_id",
        help="chat id for your private group, to view logs and errors",
    )
    parser.add_argument(
        "--leistungchat",
        dest="leistungschat_id",
        help="chat id from the main group",
    )
    parser.add_argument(
        "--eistungsadmin",
        dest="leistungsadmin_id",
        help="chat id from the admin group",
    )
    parser.add_argument(
        "--host",
        dest="mysql.host",
        help="host name/ip from the mysql server",
    )
    parser.add_argument(
        "--db",
        dest="mysql.db",
        help="databse name",
    )
    parser.add_argument(
        "--user",
        dest="mysql.user",
        help="user with access to the databse",
    )
    parser.add_argument(
        "--password",
        dest="mysql.password",
        help="user password",
    )
    parser.add_argument("--config", "-c", help="Provide a custom config file")

    args = parser.parse_args()
    lc.set_args(args, dots=True)
    print("Starting LeistungsBot")
    lb = LeistungsBot()
    lb.infinite_poll()
