from telegram import Update
from telegram.ext import ConversationHandler

from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext

async def leistungspoll(update: Update, context: LeistungsbotContext) -> int:
    await context.bot.send_message(update.effective_chat.id,
                "Schick de nexte location muaz",
                reply_markup=context.bot_data["oldlb"].helper.location_keyboard())

    return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION

async def zusatzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def konkurenzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def leistungspoll_location(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END
