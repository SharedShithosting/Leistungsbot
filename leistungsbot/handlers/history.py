from __future__ import annotations

import json

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler

from leistungsbot.Bot import LeistungsBot
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext


async def history_send_kind(
    update: Update,
    context: LeistungsbotContext,
) -> int:
    context.bot_data["oldlb"].process_history(update.message)
    return ConversationState.HISTORY_SELECT_KIND


async def history_send_leistungstag(
    update: Update,
    context: LeistungsbotContext,
) -> int:
    if update.callback_query is not None and isinstance(
        update.callback_query.data,
        str,
    ):
        data = json.loads(update.callback_query.data)
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            "Something went wrong.",
        )

    return ConversationHandler.END
