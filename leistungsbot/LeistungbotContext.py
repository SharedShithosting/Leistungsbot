from enum import IntEnum
from typing import TypedDict
from datetime import datetime

from leistungsbot.Bot import LeistungsBot

from telegram.ext import CallbackContext, ExtBot

class LeistungstagKind(IntEnum):
    NORMAL = 1
    KONKURENZ = 2
    ZUSATZ = 3

class Leistungstag:
    kind: LeistungstagKind
    location_id: int
    datetime: datetime

class UserContext(TypedDict):
    leistungstag: Leistungstag

class BotContext(TypedDict):
    oldlb: LeistungsBot

class LeistungsbotContext(CallbackContext[ExtBot, UserContext, dict, BotContext]):
    pass
