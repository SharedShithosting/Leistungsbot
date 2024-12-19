from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from leistungsbot.Bot import LeistungsBot
from leistungsbot import leistungs_config as lc

leistungsbot = LeistungsBot()

async def leistungspoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def zusatzpoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def konkurenzpoll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def send_nudes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    leistungsbot.send_nudes(update.message)
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
        ],
        states={},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    create_bot(lc.config["bot_token"])