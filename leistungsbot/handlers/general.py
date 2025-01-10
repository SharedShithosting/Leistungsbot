

from telegram import Update
from telegram.ext import ConversationHandler

from leistungsbot.LeistungbotContext import LeistungsbotContext


async def help(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def send_nudes(update: Update, context: LeistungsbotContext) -> int:
    context.bot_data["oldlb"].process_send_nudes(update.effective_chat.id)
    return ConversationHandler.END

async def cancel(update: Update, context: LeistungsbotContext) -> int:
    await context.bot.send_message(update.effective_chat.id, "Donn hoid ned. Brauchst sunst nu wos?")
    return ConversationHandler.END
