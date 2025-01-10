from __future__ import annotations

import json
from datetime import timedelta
from enum import auto
from enum import IntEnum
from typing import TypedDict

from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import Application
from telegram.ext import BaseHandler
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import ExtBot
from telegram.ext import filters
from telegram.ext import MessageHandler

import leistungsbot.Commands
import leistungsbot.handlers.general
import leistungsbot.handlers.history
import leistungsbot.handlers.polls
from leistungsbot import Commands
from leistungsbot import leistungs_config as lc
from leistungsbot.Bot import LeistungsBot
from leistungsbot.Bot import UserContext
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import BotContext
from leistungsbot.LeistungbotContext import LeistungsbotContext


async def init_bot(application: Application) -> None:
    await application.bot.set_my_commands(Commands.as_list())


async def timeout(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    await context.bot.send_message(
        update.effective_chat.id,
        "Hiaz denkst nummoi noch, wost eigentlich wüst und donn fongst nummoi vo vorn on!",
    )
    return ConversationHandler.END


def start_bot(token: str) -> None:
    application = (
        Application.builder()
        .token(token)
        .post_init(init_bot)
        .context_types(
            ContextTypes(
                context=LeistungsbotContext,
                user_data=UserContext,
                bot_data=BotContext,
            )
        )
        .build()
    )
    application.bot_data["oldlb"] = LeistungsBot()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                Commands.HELP.command, leistungsbot.handlers.general.help
            ),
            CommandHandler(
                Commands.ALIVE.command, leistungsbot.handlers.general.alive
            ),
            CommandHandler(
                Commands.VERSION.command, leistungsbot.handlers.general.version
            ),
            CommandHandler(
                Commands.MESSAGE.command, leistungsbot.handlers.general.message
            ),
            CommandHandler(
                Commands.SENDNUDES.command,
                leistungsbot.handlers.general.send_nudes,
            ),
            CommandHandler(
                Commands.LEISTUNGSPOLL.command,
                leistungsbot.handlers.polls.leistungspoll,
            ),
            CommandHandler(
                Commands.ZUSATZPOLL.command,
                leistungsbot.handlers.polls.leistungspoll,
            ),
            CommandHandler(
                Commands.KONKURRENZPOLL.command,
                leistungsbot.handlers.polls.leistungspoll,
            ),
            CommandHandler(
                Commands.HISTORY.command,
                leistungsbot.handlers.history.history_send_kind,
            ),
        ],
        states={
            ConversationState.HISTORY_SELECT_KIND: [
                CallbackQueryHandler(
                    leistungsbot.handlers.history.history_send_leistungstag
                )
            ],
            ConversationState.MESSAGE: [
                MessageHandler(
                    None, leistungsbot.handlers.general.message_send_message
                )
            ],
            ConversationState.LEISTUNGSPOLL_SELECT_LOCATION: [
                MessageHandler(
                    None, leistungsbot.handlers.polls.leistungspoll_location
                )
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(None, timeout),
                CallbackQueryHandler(timeout),
            ],
        },
        fallbacks=[
            CommandHandler(
                Commands.CANCEL.command, leistungsbot.handlers.general.cancel
            )
        ],
        conversation_timeout=timedelta(seconds=30),
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    start_bot(lc.config["bot_token"])
