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
import requests

# HELP TEXT ------------------------------------------------------------------------|
'''
User Available Commands:
    1. /poll
    2. /stats
    3. /start
    4. /help
    5. /groups
   
Developer Commands: #NOTE: ONLY @eckphi are allowed for these comands:
    1. /showIds
    2. /botlogs
'''
# MAIN VARS ------------------------------------------------------------------------|
'''
THESE ARE THE IMPORTANT VARS FOR POLL BOT
'''
BOT_TOKEN = '5277349785:AAGbCz4ozwI0l5CnkqHv2ZKhDdGi0s7Rnw0'  # YOUR BOT TOKEN HERE GET FROM @BotFather
# YOUR API HASH GET FROM my.telegram.org
API_HASH = '60f71bfe3b2f6e386597050b61ae03d7'
API_ID = '13242285'  # YOUR API ID GET FROM my.telegram.org
CHAT_ID = '-666753063'  # YOUR PRIVATE GROUP TO VIEW LOGS OR ERROR
LEISTUNGSCHAT_ID = '-1001503308928'  # '-1001517264648'
USERNAMES = ['eckphi']  # YOUR USERNAME THIS IS MANDTORY

# ABOVE MAIN VARS -------------------------------------------------------------------|
bot = telebot.TeleBot(BOT_TOKEN)


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.recent_command = None

    def excep(self, msg, error):
        bot.send_message(CHAT_ID, f'''Error From Poll Bot!

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

        return self.bot.reply_to(self.message, f'''An Unexpected Error Occured!
Error::  {error}
The error was informed to @eckphi''')

    def leistungspoll(self, msg):
        self.recent_command = 'leistungspoll'
        bot.reply_to(msg, 'Schick de nexte location muaz')

    def poller(self, message):
        try:
            with open('ltcounter.txt', 'r') as cnt:
                # The main function
                ltcounter = int(cnt.readline()) + 1
                ltdate = (datetime.datetime.now() + datetime.timedelta(days=(8 -
                          datetime.datetime.now().weekday()))).strftime('%d.%m.%Y')
                location = message.text.strip()
                question = f'Leistungstag {ltcounter}: am {ltdate} in "{location}"'

                if not location:
                    bot.reply_to(
                        message, 'Bist deppad, wüst mi veroaschn? Leistungstog im nix oda wos?')
                    return False

                id = bot.send_poll(
                    LEISTUNGSCHAT_ID,
                    question,
                    ["Bin dabei", "Keine Zeit"],
                    allows_multiple_answers=False,
                    explanation="uiuiuiui",
                    open_period=None,
                    type='quiz',
                    correct_option_id=0,
                    is_anonymous=False
                )
                with open('ltcounter.txt', 'w') as cnt:
                    cnt.write(str(ltcounter))
                with open('recentpoll.txt', 'w') as of:
                    of.write(json.dumps(
                        {'chat_id': LEISTUNGSCHAT_ID, 'message_id': id.id}))

        except IndexError:
            return bot.reply_to(message, f'''Lol!!! An error in the wild:
{message.text}

Which is invalid.
For more help use: /help
''')
        except Exception as error:
            self.excep(message, error)

    def new_msg(self, msg):
        if self.recent_command == 'leistungspoll':
            self.poller(msg)
        elif 'nude' in msg.text.lower():
            self.send_nude(msg)

    def sender_has_permission(self, msg):
        sender = bot.get_chat_member(LEISTUNGSCHAT_ID, msg.from_user.id)
        return sender.status == 'administrator' or sender.status == 'creator'

    def send_nude(self, msg):
        gif = 'https://cdn.porngifs.com/img/%s' % (random.randint(1, 39239))
        bot.send_animation(msg.chat.id, gif)
        bot.reply_to(msg, 'brought to you by Maxmaier')


cmd = Commands(bot)


@bot.message_handler(commands=['showIds'])
def showIds(message):
    try:
        if message.from_user.username in USERNAMES:
            file = open('joined_groups.txt', 'r ')
            bot.send_document(message.chat.id, file)
            file.close()

    except Exception as error:
        bot.send_message(CHAT_ID, str(error))


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
            CHAT_ID, f'Hi Devs!!\nHandle This Error plox\n{error}')
        try:
            group_ids.clear()
        except:
            pass
        bot.reply_to(message, f'An error occurred!\nError: {error}')
        bot.send_message(CHAT_ID, f'An error occurred!\nError: {error}')
        bot.send_document(CHAT_ID, '{message}')


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


@bot.message_handler(commands=['leistungspoll'])
def pollNow(message):
    if not cmd.sender_has_permission(message):
        bot.reply_to(
            message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
        return
    cmd.leistungspoll(message)


@bot.message_handler(commands=['help'])
def helper(message):
    return bot.reply_to(message, f'''
''')


@bot.message_handler(commands=['purge'])
def purge(message):
    if not cmd.sender_has_permission(message):
        bot.reply_to(
            message, 'Diese Funktion ist nicht für den Pöbel gedacht.')
        return
    try:
        with open('recentpoll.txt', 'r') as id:
            msg = json.load(id)
            bot.delete_message(msg['chat_id'], msg['message_id'])
            with open('ltcounter.txt', 'r') as cnt:
                ltcounter = int(cnt.readline()) - 1
                with open('ltcounter.txt', 'w') as cnt:
                    cnt.write(str(ltcounter))
    except IndexError:
        return bot.reply_to(message, f'''Lol!!! An error in the wild:
{message.text}

Which is invalid.
For more help use: /help
''')
    except Exception as error:
        bot.send_message(CHAT_ID, f'''Error From Poll Bot!

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


@bot.message_handler(content_types=['text'])
def new_msg(message):
    try:
        cmd.new_msg(message)
    except Exception as error:
        bot.send_message(
            CHAT_ID, f'Hi Devs!!\nHandle This Error plox\n{error}')
        bot.reply_to(message, f'An error occurred!\nError: {error}')
        bot.send_message(CHAT_ID, f'An error occurred!\nError: {error}')
        bot.send_document(CHAT_ID, '{message}')


@bot.message_handler(commands=['sendnudes'])
def send_nudes(message):
    try:
        cmd.new_msg(message)
    except Exception as error:
        bot.send_message(
            CHAT_ID, f'Hi Devs!!\nHandle This Error plox\n{error}')
        bot.reply_to(message, f'An error occurred!\nError: {error}')
        bot.send_message(CHAT_ID, f'An error occurred!\nError: {error}')
        bot.send_document(CHAT_ID, '{message}')


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
        address = "\0" + address[1:]

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


err_count = 0  # Check for errors
while True:
    try:
        bot.polling()
    except FileNotFoundError as e:
        print(e)
        err_count += 1
        print(f'Error Number: {err_count}')
        if err_count == 10:
            break
