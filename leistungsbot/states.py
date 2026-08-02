# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Conversation state, and what is remembered per user.

Its own module so the handler mixins in `leistungsbot.handlers` can name a
state without importing `Bot`, which imports them.
"""

from __future__ import annotations

from typing import TypedDict

from telebot.handler_backends import State
from telebot.handler_backends import StatesGroup


class LeistungsState(StatesGroup):
    # Just name variables differently
    normalLocation = (
        State()
    )  # creating instances of State class is enough from now
    konkurrenzLocation = State()
    zusatzLocation = State()
    searchLocation = State()
    purgeLeistungstag = State()
    historyLeistungstag = State()
    remindePoll = State()
    closePoll = State()
    sneakyClosePoll = State()
    removeLocation = State()
    rateLocation = State()
    genericLeistungsmessage = State()
    switcherooLeistungstagNumber = State()
    switcherooAlternateLocation = State()


class UserContext(TypedDict):
    leistungstag: dict | None
