from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ConversationHandler

from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext

async def leistungspoll(update: Update, context: LeistungsbotContext) -> int:
    locations = context.bot_data["oldlb"].helper.db.getVirgineLocations()

    keyboard = ReplyKeyboardMarkup.from_column([l[0] for l in reversed(locations)], one_time_keyboard=True)

    await context.bot.send_message(update.effective_chat.id,
                "Schick de nexte location muaz",
                reply_markup=keyboard)

    return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION

async def zusatzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def konkurenzpoll(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END

async def leistungspoll_location(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END
