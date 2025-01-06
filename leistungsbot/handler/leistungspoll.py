import sys
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ConversationHandler

from leistungsbot import Commands
from leistungsbot.Conversation import ConversationState
from leistungsbot.LeistungbotContext import LeistungsbotContext, Leistungstag, LeistungstagKind

async def leistungspoll(update: Update, context: LeistungsbotContext) -> int:
    if update.effective_chat is None:
        print("No effective chat in leistungpoll", file=sys.stderr)
        return ConversationHandler.END

    if context.user_data is None:
        await context.bot.send_message(update.effective_chat.id, "No userdata found")
        return ConversationHandler.END


    locations = context.bot_data["oldlb"].helper.db.getVirgineLocations()
    keyboard = ReplyKeyboardMarkup.from_column([l[0] for l in reversed(locations)], one_time_keyboard=True)

    await context.bot.send_message(update.effective_chat.id,
                "Schick de nexte location muaz",
                reply_markup=keyboard)

    lt = Leistungstag()
    if update.message is not None and update.message.text is not None:
        msg = update.message.text
        if msg.startswith(f"/{Commands.LEISTUNGSPOLL.command}"):
            lt.kind = LeistungstagKind.NORMAL
        elif msg.startswith(f"/{Commands.KONKURRENZPOLL.command}"):
            lt.kind = LeistungstagKind.KONKURENZ
        elif msg.startswith(f"/{Commands.ZUSATZPOLL.command}"):
            lt.kind = LeistungstagKind.ZUSATZ
        else:
            return ConversationHandler.END
    else:
        return ConversationHandler.END

    context.user_data["leistungstag"] = lt

    return ConversationState.LEISTUNGSPOLL_SELECT_LOCATION

async def leistungspoll_location(update: Update, context: LeistungsbotContext) -> int:
    return ConversationHandler.END
