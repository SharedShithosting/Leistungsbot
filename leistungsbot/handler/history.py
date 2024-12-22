
import json
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)


from leistungsbot.ConverstaionState import ConversationState
from leistungsbot.Bot import LeistungsBot

oldlb = LeistungsBot()

async def history_send_kind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    oldlb.process_history(update.message)
    return ConversationState.HISTORY_SELECT_KIND

async def history_send_leistungstag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query is not None and isinstance(update.callback_query.data, str):
        data = json.loads(update.callback_query.data)
    else:
        await context.bot.send_message(update.effective_chat.id, "Something went wrong.")

    return ConversationHandler.END