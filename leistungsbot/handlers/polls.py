from __future__ import annotations

import calendar
import datetime
from enum import IntEnum, auto
import json
import sys
import time

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup
from telegram import Update
from telegram.ext import ConversationHandler, ExtBot
from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_calendar import LSTEP

from leistungsbot import Commands
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext
from leistungsbot.LeistungbotContext import Leistungstag
from leistungsbot.LeistungbotContext import LeistungstagKind
from leistungsbot.LeistungbotContext import Location


class IntermediateResult(IntEnum):
    CONTINUE = auto()
    SAME_STATE = auto()
    ABORT = auto()


async def leistungspoll(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        await context.bot.send_message(
            update.effective_chat.id,
            "No userdata found",
        )
        return ConversationHandler.END

    locations = context.bot_data["oldlb"].helper.db.getVirgineLocations()
    keyboard = ReplyKeyboardMarkup.from_column(
        [l[0] for l in reversed(locations)],
        one_time_keyboard=True,
    )

    await context.bot.send_message(
        update.effective_chat.id,
        "Schick de nexte location muaz",
        reply_markup=keyboard,
    )

    lt = Leistungstag()
    if update.message is not None and update.message.text is not None:
        msg = update.message.text
        if msg.startswith(f"/{Commands.LEISTUNGSPOLL.command}"):
            lt.kind = LeistungstagKind.NORMAL
        elif msg.startswith(f"/{Commands.KONKURRENZPOLL.command}"):
            lt.kind = LeistungstagKind.KONKURENZ
        elif msg.startswith(f"/{Commands.ZUSATZPOLL.command}"):
            lt.kind = LeistungstagKind.ZUSATZ
        else:
            return ConversationHandler.END
    else:
        return ConversationHandler.END

    context.user_data["leistungstag"] = lt

    return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION


async def leistungspoll_location(
    update: Update,
    context: LeistungsbotContext,
) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        print("Userdata is missing", file=sys.stderr)
        return ConversationHandler.END

    if update.message is None or update.message.text is None:
        await context.bot.send_message(
            update.effective_chat.id,
            "Du muast a location senden",
        )
        return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION

    location_name = update.message.text.strip()
    location_info = context.bot_data["oldlb"].helper.db.getLocationInfo(
        location_name,
    )

    if location_name is None:
        await context.bot.send_message(
            update.effective_chat.id,
            f'"{location_name} kenn i ned ..',
        )
        # TODO: Jump to add_location
        return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION

    elif location_info["visited"]:
        await context.bot.send_message(
            update.effective_chat.id,
            "Do woan ma scho amal. I hoff du woast wos du duast!",
            reply_to_message_id=update.message.id,
        )

    context.user_data["leistungstag"].location = Location(
        location_info["key"],
        location_info["name"],
    )

    if context.user_data["leistungstag"].kind == LeistungstagKind.ZUSATZ:
        await send_calendar_keyboard(update.effective_chat.id, context)
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            "Für wonn damma pollen?",
            reply_markup=preselect_date_keyboard(),
        )
        return ConversationState.LEISTUNGSPOLL_PRESELECT_DATE


async def leistungpoll_preselect_date(
        update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        print("Userdata is missing", file=sys.stderr)
        return ConversationHandler.END

    if ("leistungstag" not in context.user_data
            or context.user_data["leistungstag"] is None):
        print("Leistungstag is missing", file=sys.stderr)
        return ConversationHandler.END

    if update.callback_query is None or update.callback_query.data is None:
        await context.bot.send_message(
            update.effective_chat.id, "Du muast auf de buttons drucken!"
        )
        return ConversationState.LEISTUNGSPOLL_PRESELECT_DATE

    if update.callback_query.data == "*":
        await send_calendar_keyboard(update.effective_chat.id, context)
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE

    else:
        date = datetime.datetime.fromisoformat(update.callback_query.data)
        context.user_data["leistungstag"].datetime = date
        return ConversationState.LEISTUNGSPOLL_PREVIEW


async def leistungspoll_select_date(
    update: Update, context: LeistungsbotContext
) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        print("Userdata is missing", file=sys.stderr)
        return ConversationHandler.END

    if update.callback_query is None:
        await context.bot.send_message(
            update.effective_chat.id, "Du muast auf de buttons drucken!"
        )
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE

    if update.callback_query.message is None:
        await context.bot.send_message(
            update.effective_chat.id,
            "I konn mei Nochricht nimma finden. Fong ma neich on ...",
        )
        return ConversationHandler.END

    result: datetime.date
    keyboard_json: str
    step: str
    result, keyboard_json, step = DetailedTelegramCalendar(
        min_date=datetime.date.today(),
    ).process(update.callback_query.data)

    if not result and keyboard_json:
        keyboard = InlineKeyboardMarkup.de_json(json.loads(keyboard_json))
        await context.bot.edit_message_text(
            f"Select {LSTEP[step]}",
            update.effective_chat.id,
            update.callback_query.message.message_id,
            reply_markup=keyboard,
        )

        return ConversationState.LEISTUNGSPOLL_SELECT_DATE

    elif result:
        await context.bot.edit_message_text(
            f"You selected {result}",
            update.effective_chat.id,
            update.callback_query.message.message_id,
        )

        lt_time = datetime.time(19, 0, 0)

        context.user_data["leistungstag"].datetime = datetime.datetime.combine(
            result, lt_time
        )

        if (
            context.user_data["leistungstag"].kind == LeistungstagKind.NORMAL
            or context.user_data["leistungstag"].kind
            == LeistungstagKind.KONKURENZ
        ) and result.weekday() != calendar.TUESDAY:

            await context.bot.send_message(
                update.effective_chat.id,
                "Blasphemie, des is ka Dienstag wast da du do ausgsuacht hast...alles auf eigene Gefahr!",
            )
            time.sleep(1)

        await send_leistungstag(context.bot, update.effective_chat.id, context.user_data["leistungstag"])
        # TODO: Send preview question

        return ConversationState.LEISTUNGSPOLL_PREVIEW

    print("This state should not be reached", file=sys.stderr)
    return ConversationHandler.END


async def leistungstag_preview(
    update: Update, context: LeistungsbotContext
) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        print("Userdata is missing", file=sys.stderr)
        return ConversationHandler.END

    lt = context.user_data["leistungstag"]
    location = lt.location

    if lt.datetime is None or location is None:
        await context.bot.send_message(
            update.effective_chat.id, "Hiaz hods ma in context zaumkhaut"
        )
        return ConversationHandler.END

    if dry_run:
        rand_id = self.store_to_rand_file((location, type, date))
        self.bot.send_message(
            chat_id,
            "Woin ma des so veröffentlichen?",
            reply_markup=self.dry_run_button(rand_id),
        )
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

    return ConversationHandler.END


async def send_calendar_keyboard(
     bot: ExtBot, chat_id: int
) -> None:
    calendar, step = DetailedTelegramCalendar(
        min_date=datetime.date.today(),
    ).build()
    keyboard = InlineKeyboardMarkup.de_json(json.loads(calendar))
    await bot.send_message(
        chat_id,
        f"Select {LSTEP[step]}",
        reply_markup=keyboard,
    )

async def send_leistungstag(bot: ExtBot, chat_id: int, lt: Leistungstag) -> IntermediateResult:
    if lt.datetime is None or lt.location is None:
        await bot.send_message(chat_id, "Do hob i hiaz in context verloren")
        return IntermediateResult.ABORT

    location = lt.location

    date_str = lt.datetime.strftime("%d.%m.%Y %H:%M")
    venue_id = bot.send_venue(
        chat_id,
        latitude=location.latitude,
        longitude=location.longitude,
        title=location.name,
        address=location.address,
    )

    count = 1 # TODO

    match lt.kind:
        case LeistungstagKind.NORMAL:
            kind_phrase = "Leistungstag"
        case LeistungstagKind.KONKURENZ:
            kind_phrase = "Konkurenz Leistungstag"
        case LeistungstagKind.ZUSATZ:
            kind_phrase = "Leistungstag Zusatztermin"

    poll_title = f'{kind_phrase} {count}: am {date_str} in "{location}"'

    poll_message = bot.send_poll(
        chat_id,
        poll_title,
        ["Bin dabei", "Keine Zeit"],
        allows_multiple_answers=False,
        explanation="Soi i da jez a nu erklährn wie ma obstimmt?",
        is_anonymous=False,
    )

    return IntermediateResult.CONTINUE

def get_next_tuesday() -> datetime.datetime:
    next_tuesday = datetime.datetime.now() + datetime.timedelta(
        days=(8 - datetime.datetime.now().weekday()) % 8,
    )
    return datetime.datetime(
        next_tuesday.year,
        next_tuesday.month,
        next_tuesday.day,
        19,
        0,
        0,
        0,
    )


def preselect_date_keyboard() -> InlineKeyboardMarkup:
    next_tuesday = get_next_tuesday()
    options = [
        InlineKeyboardButton(
            next_tuesday.strftime("%d.%m.%Y"),
            callback_data=next_tuesday.isoformat(),
        ),
        InlineKeyboardButton("Ondas Datum", callback_data="*"),
    ]

    return InlineKeyboardMarkup.from_column(options)

