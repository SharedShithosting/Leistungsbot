from __future__ import annotations

import sys

from telegram import Update
from telegram.ext import ConversationHandler

from leistungsbot import Commands
from leistungsbot import leistungs_config as lc
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext
from leistungsbot.package import _version


async def help(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    help_text = "Des konn i olles:\n\n"

    for command in Commands.as_list():
        help_text += f"/{command.command} - {command.description}\n"

    help_text.strip("\n")
    await context.bot.send_message(update.effective_chat.id, help_text)
    return ConversationHandler.END


async def alive(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    await context.bot.send_message(
        update.effective_chat.id,
        "Wos brauchst denn schowieder? Da papa hüft da eh ...",
    )
    return ConversationHandler.END


async def version(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    await context.bot.send_message(
        update.effective_chat.id, f"LeistungsBot - {_version.__version__}"
    )

    return ConversationHandler.END


async def message(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    await context.bot.send_message(
        update.effective_chat.id, "Wos soll i sogen?"
    )

    return ConversationState.MESSAGE


async def message_send_message(
    update: Update, context: LeistungsbotContext
) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if update.message is None or update.message.text is None:
        await context.bot.send_message(
            update.effective_chat.id, "Du soist ma nochricht schicken!"
        )
        return ConversationState.MESSAGE

    await context.bot.send_message(
        lc.config["leistungschat_id"], update.message.text
    )

    return ConversationHandler.END


async def send_nudes(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    context.bot_data["oldlb"].process_send_nudes(update.effective_chat.id)
    return ConversationHandler.END


async def cancel(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    await context.bot.send_message(
        update.effective_chat.id, "Donn hoid ned. Brauchst sunst nu wos?"
    )
    return ConversationHandler.END
