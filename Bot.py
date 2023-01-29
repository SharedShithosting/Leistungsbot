################################################################################################
################################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# @eckphi wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
################################################################################################
################################################################################################

import telebot
import datetime
import json
import os
import socket
import random
from BotHelper import Helper, LeistungsTyp
from BotScheduler import Scheduler
import yaml
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup  # States
# States storage
from telebot.storage import StateMemoryStorage
from datetime import datetime, timedelta
# Now, you can pass storage to bot.
state_storage = StateMemoryStorage()  # you can init here another storage

# HELP TEXT ------------------------------------------------------------------------|
'''
User Available Commands:
    1.  /leistungspoll
    2.  /add_location
    3.  /help
    4.  /purge
    5.  /mario
    6.  /start
    7.  /sendnudes
    8.  /rate_location
    9.  /show_participants
    10. /reminde_me
    11. /show_locations
    12. /remove_location
    13. /location_info

Developer Commands: #NOTE: ONLY @eckphi is
 allowed for these comands:
    1. /showIds
    2. /botlogs
'''
# MAIN VARS ------------------------------------------------------------------------|
'''
THESE ARE THE IMPORTANT VARS FOR POLL BOT
'''
config = yaml.safe_load(open("BotConfig.yml"))
BOT_TOKEN = config['bot_token']
# YOUR API HASH GET FROM my.telegram.org
API_HASH = config['api_hash']
API_ID = config['api_id']  # YOUR API ID GET FROM my.telegram.org
CHAT_ID = config['chat_id']  # YOUR PRIVATE GROUP TO VIEW LOGS OR ERROR
LEISTUNGSCHAT_ID = config['leistungschat_id']
LEISTUNGSADMIN_ID = config['leistungsadmin_id']
#LEISTUNGSCHAT_ID = LEISTUNGSADMIN_ID
USERNAMES = config['usernames']  # YOUR USERNAME THIS IS MANDTORY

# ABOVE MAIN VARS -------------------------------------------------------------------|


# States group.


class LeistungsState(StatesGroup):
    # Just name variables differently
    pollLocation = State()  # creating instances of State class is enough from now
    searchLocation = State()
    purgeLeistungstag = State()
    historyLeistungstag = State()
    remindePoll = State()
    closePoll = State()


class LeistungsBot(object):
    def __init__(self) -> None:
        self.bot = bot = telebot.TeleBot(config['bot_token'])
        self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))
        self.helper = Helper(self.bot)
        self.scheduler = Scheduler(self.bot)

        @bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            try:
                data = json.loads(call.data)
                if len(data) == 0:
                    bot.answer_callback_query(
                        call.id, 'SHHEEEEESH des hod ned funktioniert')
                    return
                cmd = [*data][0]
                val = [*data.values()][0]
                bot.answer_callback_query(call.id, 'Copy that')
                if cmd == 'search':
                    self.helper.approve_location(
                        call.message.chat.id, val[0], val[1])
                elif cmd == 'select':
                    if val[1] < 0:
                        if (self.helper.get_rand_len(val[0])) == 1:
                            self.bot.send_message(
                                call.message.chat.id, 'Daun füg a boa mehr infos zu deiner Suche dazua...')
                        else:
                            self.bot.send_message(call.message.chat.id, 'Daun probiern mas numoi...',
                                                  reply_markup=self.helper.restore_search_location_button(val[0]))
                    else:
                        self.helper.add_location(val[0], val[1])
                elif cmd == 'cancle':
                    self.process_cancle(call.message)
                elif cmd == 'publish':
                    self.helper.publish_leistungstag(val)
                    bot.send_message(
                        call.message.chat.id, 'Hauma so veröffentlicht')
                elif cmd == 'q':
                    self.process_search_location(call.message.chat.id, val)
                elif cmd == 'history_type':
                    self.bot.send_message(call.message.chat.id, 'Welchen Leistungstag willst da anschaun?',
                                          reply_markup=self.helper.leistungstag_history_button(LeistungsTyp(val)))
                elif cmd == 'purge_type':
                    self.bot.send_message(call.message.chat.id, 'Welchen Leistungstag willst löschen?',
                                          reply_markup=self.helper.leistungstag_dry_purge_button(LeistungsTyp(val)))
                elif cmd == 'history':
                    self.helper.send_history_info(
                        call.message.chat.id, val)
                elif cmd == 'dry_purge':
                    self.helper.send_purge_info(
                        call.message.chat.id, val)
                elif cmd == 'purge':
                    if self.helper.purge_leistungstag(val):
                        bot.send_message(
                            call.message.chat.id, 'zack und weg ises')
                    else:
                        bot.send_message(
                            call.message.chat.id, 'De Nachrichtn muast leida manuell löschen')
                elif cmd == 'open':
                    if self.bot.get_state(call.from_user.id, call.message.chat.id) == LeistungsState.remindePoll:
                        self.process_reminder(call.message, val)
                    elif self.bot.get_state(call.from_user.id, call.message.chat.id) == LeistungsState.closePoll:
                        self.process_closepoll(call.message, val)
                else:
                    bot.send_message(
                        self.helper.config['chat_id'], f'Hi Devs!!\nHandle this callback\n{cmd}')
                bot.edit_message_reply_markup(
                    call.message.chat.id, call.message.message_id)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(
                    call.message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['showIds'])
        def showIds(message):
            try:
                if message.from_user.username in USERNAMES:
                    file = open('joined_groups.txt', 'r ')
                    bot.send_document(message.chat.id, file)
                    file.close()

            except Exception as error:
                bot.send_message(self.helper.config['chat_id'], str(error))

        @bot.message_handler(commands=['stats', 'groups'])
        def stats(message):
            try:
                if message.from_user.username in USERNAMES:
                    print('Sending Stats To Owner')
                    with open('joined_groups.txt', 'r') as file:
                        group_ids = []
                        for line in file.readlines():
                            for group_id in line.split(' '):
                                group_ids.append(group_id)
                                no_of_polls = len(group_ids)
                                no_of_groups = len(list(set(group_ids)))
                        group_ids.clear()
                        bot.reply_to(
                            message, f'Number of polls Made: {no_of_polls}\n#Nr of groups bot has been added to: {no_of_groups}')
                        file.close()
                else:
                    bot.reply_to(
                        message, f'Sorry {message.from_user.username}! You Are Not Allowed To Use This Command,')
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                try:
                    group_ids.clear()
                except:
                    pass
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['botlogs'])
        def ViewTheLogsFile(message):
            try:
                if message.from_user.username in USERNAMES:
                    print('Owner Asked For The Logs!')
                    file = open('POLL_LOGS.txt', 'r')
                    bot.send_document(message.chat.id, file,
                                      timeout=60, disable_notification=True)
                    file.close()
                    print('Logs Sent To Owner')
                else:
                    bot.reply_to(
                        message, f'Sorry {message.from_user.username}! You Are Not Allowed For This Command,')
            except Exception as error:
                bot.reply_to(message, f'Error: {error}')

        @bot.message_handler(commands=['help'])
        def helper(message):
            return bot.reply_to(message, f'''Eiso i hüf da do ned...''')

        @bot.message_handler(commands=['purge'])
        def purge(message):
            if not self.helper.sender_has_permission(message):
                bot.reply_to(
                    message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
                return
            try:
                self.process_purge(message)
            except IndexError:
                return bot.reply_to(message, f'''Lol!!! An error in the wild:
        {message.text}

        Which is invalid.
        For more help use: /help
        ''')
            except Exception as error:
                bot.send_message(self.helper.config['chat_id'], f'''Error From Poll Bot!

        Error  :: {error}

        --------------------------------

        Command:: {message.text}

        --------------------------------

        UserDetails: {message.from_user}

        --------------------------------

        Date   :: {message.date}

        --------------------------------

        The Complete Detail:
        {message}


        ''')

                return bot.reply_to(message, f'''An Unexpected Error Occured!
        Error::  {error}
        The error was informed to @eckphi''')

        @bot.message_handler(commands=['alive'])
        def alive(message):
            bot.reply_to(
                message, f'Hey {message.from_user.username}, Ready To Serve You')

        @bot.message_handler(commands=['start'])
        def start(message):
            bot.reply_to(
                message, f'Heya {message.from_user.username}, I am there to help you in polls. But this cmd is bit old try /help.')

        @bot.message_handler(commands=['leistungspoll'])
        def pollNow(message):
            try:
                self.process_leistungspoll(message)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['sendreminder'])
        def pollNow(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
                    return

                self.bot.set_state(message.from_user.id,
                        LeistungsState.pollLocation, message.chat.id)
                self.bot.reply_to(message, 'An welchen Poll wüst reminden?',
                reply_markup=self.helper.open_polls_button())
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['closepoll'])
        def pollNow(message):
            try:
                if not self.helper.sender_has_permission(message):
                    self.bot.reply_to(
                        message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
                    return

                self.bot.set_state(message.from_user.id,
                        LeistungsState.pollLocation, message.chat.id)
                self.bot.reply_to(message, 'An welchen Poll wüst closen?',
                    reply_markup=self.helper.open_polls_button())
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['sendnudes'])
        def send_nudes(message):
            try:
                self.process_send_nudes(message.chat.id)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['add_location'])
        def request_location(message):
            try:
                self.bot.set_state(message.from_user.id,
                                   LeistungsState.searchLocation, message.chat.id)
                self.bot.send_message(
                    message.chat.id, 'Schick dei location idee muaz')
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(commands=['history'])
        def request_location(message):
            try:
                self.process_history(message)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(state="*", commands=['cancle'])
        def cancel(message):
            try:
                self.process_cancle(message)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(state=LeistungsState.pollLocation)
        def getPollLocation(message):
            try:
                self.process_poll_location(message)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(state=LeistungsState.searchLocation)
        def search_location(message):
            try:
                self.process_search_location(
                    message.chat.id, message.text.strip())
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

        @bot.message_handler(content_types=['text'])
        def new_msg(message):
            try:
                if 'nude' in message.text:
                    self.process_send_nudes(message.chat.id)
            except Exception as error:
                bot.send_message(
                    self.helper.config['chat_id'], f'Hi Devs!!\nHandle This Error plox\n{error}')
                bot.reply_to(message, f'An error occurred!\nError: {error}')
                bot.send_message(
                    self.helper.config['chat_id'], f'An error occurred!\nError: {error}')

    def process_cancle(self, message):
        self.bot.send_message(message.chat.id, "Halt Stop.",
                              reply_markup=telebot.types.ReplyKeyboardRemove())
        self.bot.delete_state(message.from_user.id, message.chat.id)

    def process_leistungspoll(self, message):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
            return
        self.bot.set_state(message.from_user.id,
                           LeistungsState.pollLocation, message.chat.id)
        self.bot.send_message(message.chat.id, 'Schick de nexte location muaz',
                              reply_markup=self.helper.location_keyboard())

    def process_poll_location(self, message):
        location = message.text.strip()
        # check if location exists in database
        info = self.helper.db.getLocationInfo(location)
        if not info:
            self.bot.send_message(
                message.chat.id, f"'{location}' kenn i ned..wüstas stattdessn zur listn dazua gebn?",
                reply_markup=self.helper.unkown_location_button(location))
            self.bot.set_state(message.from_user.id,
                               LeistungsState.searchLocation, message.chat.id)
        else:
            self.helper.send_leistungstag(message.chat.id, location)
            self.bot.delete_state(message.from_user.id, message.chat.id)

    def process_reminder(self, message, leistungstag_key):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
            return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.bot.send_message(
            self.config['leistungschat_id'], 'Reminder. Morgen wird reserviert. Letzte Chance zum Abstimmen 🗳️', reply_to_message_id=leistungstag['poll_id'])
        self.bot.send_message(message.chat.id, 'Da Reminder is draußen!')

    def process_closepoll(self, message, leistungstag_key):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
            return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.bot.stop_poll(
            self.config['leistungschat_id'], leistungstag['poll_id'])
        self.bot.send_message(
            self.config['leistungschat_id'], 'Schluss, aus, vorbei die Wahl is glaufen und für de de abgstimmt haben is a Platzerl reserviert.', reply_to_message_id=leistungstag['poll_id'])
        self.bot.send_message(message.chat.id, 'De Poll is zua. I hoff für dich d Reservierung is scho erledigt!')

    def process_send_nudes(self, message):
        self.helper.send_nude(message)

    def process_search_location(self, chat_id, query):
        finds, rand_id = self.helper.search_location(query)
        if finds < 1:
            self.bot.send_message(
                chat_id, f'Wenn i nach "{query}" suach find i nix...vielleicht verschriebn?')
        elif finds == 1:
            self.helper.approve_location(chat_id, rand_id, 0)
        elif finds > 1:
            self.bot.send_message(chat_id, 'Suach da aus wost willst, oda schick ma wos aunders',
                                  reply_markup=self.helper.search_location_button(rand_id))

    def process_history(self, message):
        self.bot.send_message(message.chat.id, 'Welche Art von Leistungstag willst da anschaun?',
                              reply_markup=self.helper.leistungstag_history_type_button())

    def process_purge(self, message):
        self.bot.send_animation(
            message.chat.id, 'https://giphy.com/gifs/MCZ39lz83o5lC',
            caption='Welche Art von Leistungstag willst löschen?',
            reply_markup=self.helper.leistungstag_purge_type_button())

    def infinite_poll(self):
        self.bot.infinity_polling()

    def poll(self):
        self.bot.polling()


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


def watchdog_period():
    """Return the time (in seconds) that we need to ping within."""
    val = os.environ.get("WATCHDOG_USEC", None)
    if not val:
        logger.error("No watchdog period set in the unit file.")
        return 1
    return max([int(val)/1000000, 1])


def notify_socket(clean_environment=True):
    """Return a tuple of address, socket for future use.
    clean_environment removes the variables from env to prevent children
    from inheriting it and doing something wrong.
    """
    _empty = None, None
    address = os.environ.get("NOTIFY_SOCKET", None)
    if clean_environment:
        address = os.environ.pop("NOTIFY_SOCKET", None)

    if not address:
        return _empty

    if len(address) == 1:
        return _empty

    if address[0] not in ("@", "/"):
        return _empty

    if address[0] == "@":
        address = "\0" + str(address[1:])

    # SOCK_CLOEXEC was added in Python 3.2 and requires Linux >= 2.6.27.
    # It means "close this socket after fork/exec()
    try:
        sock = socket.socket(socket.AF_UNIX,
                             socket.SOCK_DGRAM | socket.SOCK_CLOEXEC)
    except AttributeError:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    return address, sock


def sd_message(address, sock, message):
    """Send a message to the systemd bus/socket.
    message is expected to be bytes.
    """
    if not (address and sock and message):
        return False
    assert isinstance(message, bytes)

    try:
        retval = sock.sendto(message, address)
    except socket.error:
        return False
    return (retval > 0)


def watchdog_ping(address, sock):
    """Helper function to send a watchdog ping."""
    message = b"WATCHDOG=1"
    return sd_message(address, sock, message)


def systemd_ready(address, sock):
    """Helper function to send a ready signal."""
    message = b"READY=1"
    logger.debug("Signaling system ready")
    return sd_message(address, sock, message)


def systemd_stop(address, sock):
    """Helper function to signal service stopping."""
    message = b"STOPPING=1"
    return sd_message(address, sock, message)


def systemd_status(address, sock, status):
    """Helper function to update the service status."""
    message = ("STATUS=%s" % status).encode('utf8')
    return sd_message(address, sock, message)


if __name__ == '__main__':
    lb = LeistungsBot()
    lb.infinite_poll()
