from telegram import Update
from telegram.ext import ConversationHandler

from leistungsbot.LeistungbotContext import LeistungsbotContext

async def leistungspoll_send_locations(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def zusatzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def konkurenzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END
