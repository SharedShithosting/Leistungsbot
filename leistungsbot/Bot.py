# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
from __future__ import annotations

import argparse
import logging
from datetime import datetime

import telebot
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
from telegram_bot_calendar import DetailedTelegramCalendar

from leistungsbot import Commands
from leistungsbot import leistungs_config as lc
from leistungsbot.BotHelper import Helper
from leistungsbot.BotScheduler import Scheduler
from leistungsbot.handlers.admin import AdminHandlers
from leistungsbot.handlers.callbacks import CallbackHandlers
from leistungsbot.handlers.general import GeneralHandlers
from leistungsbot.handlers.history import HistoryHandlers
from leistungsbot.handlers.lifecycle import PollLifecycleHandlers
from leistungsbot.handlers.locations import LocationHandlers
from leistungsbot.handlers.polls import PollHandlers
from leistungsbot.states import LeistungsState
from leistungsbot.states import UserContext

# States storage
# Now, you can pass storage to bot.
state_storage = StateMemoryStorage()  # you can init here another storage

# The hand written command list that used to sit here is gone - it had
# drifted far enough to advertise /mario, /show_participants, /reminde_me
# and /location_info, none of which have a handler. leistungsbot.Commands is
# the list now, and /help prints it.

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.


class LeistungsBot(
    GeneralHandlers,
    PollHandlers,
    PollLifecycleHandlers,
    LocationHandlers,
    HistoryHandlers,
    AdminHandlers,
    CallbackHandlers,
):
    """! The bot itself: the collaborators, and the handler wiring.

    The handlers live in `leistungsbot.handlers`, one module per workflow.
    They are mixed in rather than held as separate objects because they all
    reach for the same bot, helper and per user state.
    """

    #: Handler methods in registration order, see `register_handlers`.
    #: Kept as names rather than functions so the table can live on the
    #: class, right next to the methods it lists.
    MESSAGE_HANDLERS = (
        ("showIds", {"commands": Commands.SHOW_IDS.names}),
        ("stats", {"commands": Commands.STATS.names}),
        ("ViewTheLogsFile", {"commands": Commands.BOTLOGS.names}),
        ("help_command", {"commands": Commands.HELP.names}),
        ("purge", {"commands": Commands.PURGE.names}),
        ("alive", {"commands": Commands.ALIVE.names}),
        ("start", {"commands": Commands.START.names}),
        ("poll_now", {"commands": Commands.LEISTUNGSPOLL.names}),
        ("zusatz_poll", {"commands": Commands.ZUSATZPOLL.names}),
        ("konkurrenz_poll", {"commands": Commands.KONKURRENZPOLL.names}),
        ("send_reminder", {"commands": Commands.SENDREMINDER.names}),
        ("close_poll", {"commands": Commands.CLOSEPOLL.names}),
        ("sneaky_close_poll", {"commands": Commands.SNEAKY_CLOSEPOLL.names}),
        ("send_nudes", {"commands": Commands.SENDNUDES.names}),
        ("add_location", {"commands": Commands.ADD_LOCATION.names}),
        ("backup", {"commands": Commands.BACKUP.names}),
        (
            "remove_location_handler",
            {"commands": Commands.REMOVE_LOCATION.names},
        ),
        ("history", {"commands": Commands.HISTORY.names}),
        ("rate_location_handler", {"commands": Commands.RATE_LOCATION.names}),
        ("show_locations", {"commands": Commands.SHOW_LOCATIONS.names}),
        ("message_command", {"commands": Commands.MESSAGE.names}),
        ("cancel", {"state": "*", "commands": Commands.CANCEL.names}),
        ("get_poll_location", {"state": LeistungsState.normalLocation}),
        (
            "get_konkurrenz_location",
            {"state": LeistungsState.konkurrenzLocation},
        ),
        ("get_zusatz_location", {"state": LeistungsState.zusatzLocation}),
        ("remove_location", {"state": LeistungsState.removeLocation}),
        ("search_location", {"state": LeistungsState.searchLocation}),
        ("rate_location", {"state": LeistungsState.rateLocation}),
        (
            "switcheroo_leistungstag_number",
            {"state": LeistungsState.switcherooLeistungstagNumber},
        ),
        (
            "switcheroo_alternate_location",
            {"state": LeistungsState.switcherooAlternateLocation},
        ),
        ("switcheroo", {"commands": Commands.SWITCHEROO.names}),
        ("version", {"commands": Commands.VERSION.names}),
    )

    def __init__(self) -> None:
        self.bot = telebot.TeleBot(lc.config["bot_token"])
        self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))
        self.helper = Helper(self.bot)
        self.scheduler = Scheduler(self.bot, self.helper)
        self.poller = None
        self.last_text_nudes = datetime.min
        self.user_context: dict[int, UserContext] = {}
        self.register_handlers()

    def register_handlers(self) -> None:
        """! Points telebot at the handler methods, in order

        The order is load bearing and always was - it just used to be
        implied by where a `def` happened to sit in a 900 line `__init__`.
        Telebot dispatches to the first handler that matches, so a state
        handler listed above a command handler swallows that command.
        Reordering this list changes behaviour.
        """
        bot = self.bot

        bot.register_callback_query_handler(
            self.cal,
            func=DetailedTelegramCalendar.func(),
        )
        bot.register_callback_query_handler(
            self.callback_query,
            func=self.helper.filter(),
        )

        for handler, kwargs in self.MESSAGE_HANDLERS:
            # `@bot.message_handler` defaults content_types to text,
            # `register_message_handler` hands the None straight through and
            # a handler without content types matches every kind of message.
            # Passing it explicitly keeps these handlers text only.
            bot.register_message_handler(
                getattr(self, handler),
                content_types=["text"],
                **kwargs,
            )

    def infinite_poll(self):
        self.bot.infinity_polling()

    def poll(self):
        self.bot.polling()


def main():
    parser = argparse.ArgumentParser(
        description="LeistungsBot - some realy weird bot.",
    )
    parser.add_argument(
        "--google",
        "-g",
        dest="google",
        help="Google api key",
    )
    parser.add_argument(
        "--token",
        "-t",
        dest="bot_token",
        help="Telegram bot token generated by @BotFather",
    )
    parser.add_argument(
        "--hash",
        dest="api_hash",
        help="api hash from my.telegram.org",
    )
    parser.add_argument(
        "--id",
        dest="api_id",
        help="api id from my.telegram.org",
    )
    parser.add_argument(
        "--chat",
        dest="chat_id",
        help="chat id for your private group, to view logs and errors",
    )
    parser.add_argument(
        "--leistungchat",
        dest="leistungschat_id",
        help="chat id from the main group",
    )
    parser.add_argument(
        "--eistungsadmin",
        dest="leistungsadmin_id",
        help="chat id from the admin group",
    )
    parser.add_argument(
        "--db",
        dest="sqlite.path",
        help="path to the sqlite database file",
    )
    parser.add_argument("--config", "-c", help="Provide a custom config file")

    args = parser.parse_args()
    lc.set_args(args, dots=True)
    print("Starting LeistungsBot")
    lb = LeistungsBot()
    lb.publish_commands()
    lb.infinite_poll()
