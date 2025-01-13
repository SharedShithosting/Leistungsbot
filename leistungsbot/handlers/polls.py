from __future__ import annotations

import sys
from datetime import datetime
from datetime import timedelta

from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup
from telegram import Update
from telegram.ext import ConversationHandler

from leistungsbot import Commands
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext
from leistungsbot.LeistungbotContext import Leistungstag
from leistungsbot.LeistungbotContext import LeistungstagKind
from leistungsbot.LeistungbotContext import Location


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

    context.user_data["location"] = Location(
        location_info["key"],
        location_info["name"],
    )

    if context.user_data["leistungstag"].kind == LeistungstagKind.ZUSATZ:
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE
    else:
        leistungstag_date = get_next_tuesday()

        return ConversationState.LEISTUNGSPOLL_PRESELECT_DATE


def get_next_tuesday() -> datetime:
    next_tuesday = datetime.now() + timedelta(
        days=(8 - datetime.now().weekday()) % 8,
    )
    return datetime(
        next_tuesday.year,
        next_tuesday.month,
        next_tuesday.day,
        19,
        0,
        0,
        0,
    )


def preselect_date_keyboard() -> InlineKeyboardMarkup:
    pass
