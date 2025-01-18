from __future__ import annotations

import json
import sys
from datetime import date, datetime
from datetime import timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup
from telegram import Update
from telegram.ext import ConversationHandler

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

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
        calendar, step = DetailedTelegramCalendar(
            min_date=date.today(),
        ).build()
        keyboard = InlineKeyboardMarkup.de_json(json.loads(calendar))
        await context.bot.send_message(
            update.effective_chat.id,
            f"Select {LSTEP[step]}",
            reply_markup=keyboard,
        )
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE
    else:
        await context.bot.send_message(update.effective_chat.id, "Für wonn damma pollen?", reply_markup=preselect_date_keyboard())
        return ConversationState.LEISTUNGSPOLL_PRESELECT_DATE

async def leistungspoll_select_date(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    # if context.user_data is None:
    #     print("Userdata is missing", file=sys.stderr)
    #     return ConversationHandler.END

    if update.callback_query is None:
        await context.bot.send_message(update.effective_chat.id, "Du muast auf de buttons drucken!")
        return ConversationState.LEISTUNGSPOLL_SELECT_DATE

    if update.callback_query.message is None:
        await context.bot.send_message(update.effective_chat.id, "I konn mei Nochricht nimma finden. Fong ma neich on ...")
        return ConversationHandler.END

    result, calendar, step = DetailedTelegramCalendar(
        min_date=date.today(),
    ).process(update.callback_query.data)

    if not result and calendar:
        keyboard = InlineKeyboardMarkup.de_json(json.loads(calendar))
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

        return ConversationState.LEISTUNGSPOLL_PREVIEW

    return 0


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
    next_tuesday = get_next_tuesday()
    options = [InlineKeyboardButton(next_tuesday.strftime("%d.%m.%Y"), callback_data=next_tuesday.isoformat()),
                InlineKeyboardButton("Ondas Datum", callback_data="*")]

    return InlineKeyboardMarkup.from_column(options)
