from __future__ import annotations

from telegram import BotCommand

# General
HELP = BotCommand("help", "Display help message")
ALIVE = BotCommand("alive", "Check if I am up")
VERSION = BotCommand("version", "Display help message")
MESSAGE = BotCommand("message", "Send custom message")
SENDNUDES = BotCommand("send_nudes", "😈")
CANCEL = BotCommand("cancel", "Cancel current conversation")

# Polls/Leistungstage
LEISTUNGSPOLL = BotCommand("leistungspoll", "Create a new poll for next week")
KONKURRENZPOLL = BotCommand(
    "konkurrenzpoll", "Create a new konkurrenz poll for next week"
)
ZUSATZPOLL = BotCommand("zusatzpoll", "Create a new zusatz poll")
CLOSEPOLL = BotCommand("poll_close", "Close a poll")
SNEAKY_CLOSEPOLL = BotCommand(
    "poll_close_sneaky", "Close a poll without any notification"
)
PURGE = BotCommand("poll_purge", "Delete a poll")
HISTORY = BotCommand("poll_history", "Show past leistungstage")

# Locations
LOCATION_ADD = BotCommand("location_add", "Add a new location recommendation")
LOCATION_REMOVE = BotCommand("location_remove", "Remove a unvisited location")
LOCATIONS_SHOW = BotCommand("locations_show", "Show unvisited locations")
LOCATION_RATE = BotCommand("location_rate", "Rate the most recent location")


def as_list() -> list[BotCommand]:
    # Python hack to get all the BotCommands defined above as list
    return [
        item for item in globals().values() if isinstance(item, BotCommand)
    ]


if __name__ == "__main__":
    print(as_list())
