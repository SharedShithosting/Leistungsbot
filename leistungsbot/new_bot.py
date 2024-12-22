from datetime import timedelta
from enum import IntEnum, auto
import json
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    BaseHandler,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from leistungsbot import leistungs_config as lc
from leistungsbot.Bot import LeistungsBot
from leistungsbot.ConverstaionState import ConversationState

import leistungsbot.handler

old = LeistungsBot()

async def leistungspoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def zusatzpoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def konkurenzpoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def send_nudes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    old.process_send_nudes(update.effective_chat.id)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

def create_bot(token: str):
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("leistungspoll", leistungspoll),
            CommandHandler("zusatzpoll", zusatzpoll),
            CommandHandler("konkurenzpoll", konkurenzpoll),
            CommandHandler("help", help),
            CommandHandler("sendnudes", send_nudes),
            CommandHandler("histroy", leistungsbot.handler.history_send_kind),
        ],
        states={
            ConversationState.HISTORY_SELECT_KIND: [CallbackQueryHandler(leistungsbot.handler.history_send_leistungstag)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=timedelta(minutes=5)
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    create_bot(lc.config["bot_token"])