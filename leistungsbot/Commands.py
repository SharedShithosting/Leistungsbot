# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Every command the bot answers to, in one place.

Until now a command existed in exactly one spot: the string inside its
``@bot.message_handler(commands=[...])`` decorator, roughly 900 lines deep
into ``LeistungsBot.__init__``. Nothing could enumerate them, which is why
``/help`` answered with a joke and why telegram never showed a command menu -
``set_my_commands`` was never called because there was no list to pass it.

The registry below is that list. ``Bot.py`` registers its handlers from it, so
the two cannot drift apart: rename a command here and the handler follows.

Deliberately free of any telegram library import. ``as_telebot`` is the only
place that knows about pyTelegramBotAPI, so the eventual move to
python-telegram-bot (#45) replaces one function instead of the registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

import telebot


class Access(Enum):
    """Who gets to run a command.

    This mirrors the checks the handlers already perform, it does not
    enforce anything - the handler stays responsible for that. It only
    decides who is told the command exists.
    """

    #: anyone in the chat
    PUBLIC = "public"
    #: an administrator of the leistungschat, via ``sender_has_permission``
    ADMIN = "admin"
    #: a username from the ``usernames`` config key, the maintenance commands
    OWNER = "owner"


@dataclass(frozen=True)
class Command:
    """A single command, without the leading slash."""

    command: str
    description: str
    access: Access = Access.PUBLIC
    #: further names the same handler answers to
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def names(self) -> list[str]:
        """What ``@bot.message_handler(commands=...)`` expects."""
        return [self.command, *self.aliases]


# --- general -----------------------------------------------------------
HELP = Command("help", "Display help message")
START = Command("start", "Say hello")
ALIVE = Command("alive", "Check if I am up")
VERSION = Command("version", "Show the running version")
CANCEL = Command(
    "cancel",
    "Cancel current conversation",
)
SENDNUDES = Command("sendnudes", "😈")
MESSAGE = Command("message", "Send custom message", Access.ADMIN)

# --- polls / leistungstage ---------------------------------------------
LEISTUNGSPOLL = Command(
    "leistungspoll",
    "Create a new poll for next week",
    Access.ADMIN,
)
KONKURRENZPOLL = Command(
    "konkurrenzpoll",
    "Create a new konkurrenz poll for next week",
    Access.ADMIN,
)
ZUSATZPOLL = Command("zusatzpoll", "Create a new zusatz poll", Access.ADMIN)
CLOSEPOLL = Command("closepoll", "Close a poll", Access.ADMIN)
SNEAKY_CLOSEPOLL = Command(
    "sneaky_closepoll",
    "Close a poll without any notification",
    Access.ADMIN,
)
PURGE = Command("purge", "Delete a poll", Access.ADMIN)
HISTORY = Command("history", "Show past leistungstage")
SENDREMINDER = Command(
    "sendreminder",
    "Remind the chat about a poll",
    Access.ADMIN,
)
SWITCHEROO = Command(
    "switcheroo",
    "Move a leistungstag to another location",
    Access.ADMIN,
)

# --- locations ---------------------------------------------------------
ADD_LOCATION = Command("add_location", "Add a new location recommendation")
REMOVE_LOCATION = Command(
    "remove_location",
    "Remove a unvisited location",
    Access.ADMIN,
)
SHOW_LOCATIONS = Command("show_locations", "Show unvisited locations")
RATE_LOCATION = Command("rate_location", "Rate the most recent location")

# --- maintenance -------------------------------------------------------
BACKUP = Command("backup", "Send a copy of the database", Access.ADMIN)
BOTLOGS = Command("botlogs", "Send the log file", Access.OWNER)
SHOW_IDS = Command("showIds", "Send the list of joined groups", Access.OWNER)
STATS = Command(
    "stats",
    "Show the groups I am a member of",
    Access.OWNER,
    aliases=("groups",),
)

#: Order matters, this is the order ``/help`` and telegram's menu use.
ALL: tuple[Command, ...] = (
    HELP,
    START,
    ALIVE,
    VERSION,
    CANCEL,
    SENDNUDES,
    MESSAGE,
    LEISTUNGSPOLL,
    KONKURRENZPOLL,
    ZUSATZPOLL,
    CLOSEPOLL,
    SNEAKY_CLOSEPOLL,
    PURGE,
    HISTORY,
    SENDREMINDER,
    SWITCHEROO,
    ADD_LOCATION,
    REMOVE_LOCATION,
    SHOW_LOCATIONS,
    RATE_LOCATION,
    BACKUP,
    BOTLOGS,
    SHOW_IDS,
    STATS,
)


def visible_to(access: Access) -> list[Command]:
    """The commands somebody with `access` should be told about.

    An admin sees the public commands as well, an owner sees everything.
    """
    if access is Access.OWNER:
        return list(ALL)
    if access is Access.ADMIN:
        return [c for c in ALL if c.access is not Access.OWNER]
    return [c for c in ALL if c.access is Access.PUBLIC]


def as_telebot(commands: list[Command]) -> list[telebot.types.BotCommand]:
    """The registry in the shape ``TeleBot.set_my_commands`` wants.

    Aliases are left out on purpose: telegram shows this list as the command
    menu, and two entries running the same handler only take up room.
    """
    return [
        telebot.types.BotCommand(c.command, c.description) for c in commands
    ]


def help_text(access: Access = Access.PUBLIC) -> str:
    """The body of ``/help``, tailored to what the sender may run."""
    lines = [f"/{c.command} - {c.description}" for c in visible_to(access)]
    return "\n".join(lines)
