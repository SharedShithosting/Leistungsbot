from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import TypedDict

from telegram.ext import CallbackContext
from telegram.ext import ExtBot

from leistungsbot.Bot import LeistungsBot


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


class LeistungsbotContext(
    CallbackContext[ExtBot, UserContext, dict, BotContext]
):
    pass
