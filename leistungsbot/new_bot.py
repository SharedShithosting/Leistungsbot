from datetime import timedelta
from enum import IntEnum, auto
import json
from typing import TypedDict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    BaseHandler,
    CallbackQueryHandler,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    ExtBot,
    MessageHandler,
    filters,
)

from leistungsbot import leistungs_config as lc
from leistungsbot.Bot import LeistungsBot
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext, BotContext

import leistungsbot.handler


async def help(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def send_nudes(update: Update, context: LeistungsbotContext) -> int:
    context.bot_data["oldlb"].process_send_nudes(update.effective_chat.id)
    return ConversationHandler.END

async def cancel(update: Update, context: LeistungsbotContext) -> int:
    await context.bot.send_message(update.effective_chat.id, "Donn hoid ned. Brauchst sunst nu wos?")
    return ConversationHandler.END

async def timeout(update: Update, context: LeistungsbotContext) -> int:
    await context.bot.send_message(update.effective_chat.id, "Hiaz denkst nummoi noch, wost eigentlich wüst und donn fongst nummoi vo vorn on!")
    return ConversationHandler.END

def start_bot(token: str) -> None:
    application = Application.builder().token(token).context_types(ContextTypes(context=LeistungsbotContext, bot_data=BotContext)).build()
    application.bot_data["oldlb"] = LeistungsBot()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("leistungspoll", leistungsbot.handler.leistungspoll),
            CommandHandler("zusatzpoll", leistungsbot.handler.zusatzpoll),
            CommandHandler("konkurenzpoll", leistungsbot.handler.konkurenzpoll),
            CommandHandler("help", help),
            CommandHandler("sendnudes", send_nudes),
            CommandHandler("history", leistungsbot.handler.history_send_kind),
        ],
        states={
            ConversationState.HISTORY_SELECT_KIND: [CallbackQueryHandler(leistungsbot.handler.history_send_leistungstag)],
            ConversationHandler.TIMEOUT: [MessageHandler(None, timeout), CallbackQueryHandler(timeout)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=timedelta(seconds=30)
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    create_bot(lc.config["bot_token"])
