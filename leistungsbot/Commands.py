from telegram import BotCommand

# General
HELP = BotCommand("help", "Display help message")
ALIVE = BotCommand("alive", "Check if I am up")
VERSION = BotCommand("version", "Display help message")
MESSAGE = BotCommand("message", "Send custom message")
SENDNUDES = BotCommand("sendnudes", "😈")
CANCEL = BotCommand("cancel", "Cancel current conversation")

# Polls/Leistungstage
LEISTUNGSPOLL = BotCommand("leistungspoll", "Create a new poll for next week")
KONKURRENZPOLL = BotCommand("konkurrenzpoll", "Create a new konkurrenz poll for next week")
ZUSATZPOLL = BotCommand("zusatzpoll", "Create a new zusatz poll")
CLOSEPOLL = BotCommand("closepoll", "Close a poll")
SNEAKY_CLOSEPOLL = BotCommand("sneaky_closepoll", "Close a poll without any notification")
PURGE = BotCommand("purge", "Delete a poll")
HISTORY = BotCommand("history", "Show past leistungstage")

# Locations
ADD_LOCATION = BotCommand("add_location", "Add a new location recommendation")
REMOVE_LOCATION = BotCommand("remove_location", "Remove a unvisited location")
SHOW_LOCATION = BotCommand("show_location", "Show unvisited locations")
RATE_LOCATION = BotCommand("rate_location", "Rate the most recent location")

def as_list() -> list[BotCommand]:
    # Python hack to get all the BotCommands defined above as list
    return [item for item in globals().values() if isinstance(item, BotCommand)]

if __name__ == "__main__":
    print(as_list())
