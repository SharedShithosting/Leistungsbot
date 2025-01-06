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

from leistungsbot import leistungs_config as lc, Commands
from leistungsbot.Bot import LeistungsBot, UserContext
import leistungsbot.Commands
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext, BotContext

import leistungsbot.handlers.history
import leistungsbot.handlers.polls

async def init_bot(application: Application) -> None:
    await application.bot.set_my_commands(Commands.as_list())

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
    application = Application.builder().token(token).post_init(init_bot).context_types(ContextTypes(context=LeistungsbotContext, user_data=UserContext, bot_data=BotContext)).build()
    application.bot_data["oldlb"] = LeistungsBot()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(Commands.LEISTUNGSPOLL.command, leistungsbot.handlers.polls.leistungspoll),
            CommandHandler(Commands.ZUSATZPOLL.command, leistungsbot.handlers.polls.leistungspoll),
            CommandHandler(Commands.KONKURRENZPOLL.command, leistungsbot.handlers.polls.leistungspoll),
            CommandHandler(Commands.HELP.command, help),
            CommandHandler(Commands.SENDNUDES.command, send_nudes),
            CommandHandler(Commands.HISTORY.command, leistungsbot.handlers.history.history_send_kind),
        ],
        states={
            ConversationState.HISTORY_SELECT_KIND: [CallbackQueryHandler(leistungsbot.handlers.history.history_send_leistungstag)],
            ConversationState.LEISTUNGSPOLL_SELECT_LOCATION: [MessageHandler(None, leistungsbot.handlers.polls.leistungspoll_location)],
            ConversationHandler.TIMEOUT: [MessageHandler(None, timeout), CallbackQueryHandler(timeout)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=timedelta(seconds=30)
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    start_bot(lc.config["bot_token"])
