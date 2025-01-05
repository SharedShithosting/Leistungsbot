from typing import TypedDict
from leistungsbot.Bot import LeistungsBot

from telegram.ext import CallbackContext, ExtBot


class BotContext(TypedDict):
    oldlb: LeistungsBot

class LeistungsbotContext(CallbackContext[ExtBot, dict, dict, BotContext]):
    pass
