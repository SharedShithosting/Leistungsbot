# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The commands that are not about a leistungstag at all."""

from __future__ import annotations

import logging

import telebot

from leistungsbot import Commands
from leistungsbot import _version
from leistungsbot import leistungs_config as lc
from leistungsbot.states import LeistungsState

#: Every name telebot will match as a command, aliases included.
KNOWN_COMMANDS = frozenset(
    name for command in Commands.ALL for name in command.names
)


class GeneralHandlers:
    """The commands that are not about a leistungstag at all."""

    def is_unknown_command(self, message) -> bool:
        """! Whether `message` is a command nothing above this handles

        Telebot has no such filter: a command handler matches its own
        names and that is all, so anything starting with a slash that is
        not in the registry fell through to whichever state handler was
        listening and was read as an answer. A typo in the middle of
        /add_location became a location name. See #17.
        """
        text = (message.text or "").strip()
        if not text.startswith("/"):
            return False
        word = text.split(maxsplit=1)[0]
        # telegram lets a command be addressed at a bot: /help@leistungsbot
        return word[1:].split("@", 1)[0] not in KNOWN_COMMANDS

    def unknown_command(self, message):
        """! Answers a command that does not exist

        Does not end the conversation. A mistyped command is the one case
        where the sender clearly did not mean to start something new, and
        dropping their half finished workflow over a typo would be worse
        than the typo.
        """
        self.bot.reply_to(
            message,
            "So an Befehl hob i ned. Schau amoi in /help eine.",
        )

    def help_command(self, message):
        try:
            return self.bot.reply_to(
                message,
                "Eiso i hüf da do ned...na guat, do host:\n\n"
                + Commands.help_text(self.access_of(message)),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def alive(self, message):
        self.bot.reply_to(
            message,
            f"Hey {message.from_user.username}, Ready To Serve You in version {_version.__version__}",
        )

    def start(self, message):
        self.bot.reply_to(
            message,
            f"Heya {message.from_user.username}, I am there to help you in polls. But this cmd is bit old try /help.",
        )

    def version(self, message):
        self.bot.reply_to(
            message,
            f"LeistungsBot - {_version.__version__}",
        )

    def cancel(self, message):
        try:
            self.process_cancel(message)
        except Exception as error:
            self.helper.report_error(message, error)

    def send_nudes(self, message):
        try:
            if message.chat.type != "private":
                self.bot.reply_to(
                    message,
                    "Bist deppad? Des is nix fürn Gruppen chat, du Drecksau.",
                )
            else:
                self.process_send_nudes(message.chat.id)
        except Exception as error:
            self.helper.report_error(message, error)

    def message_command(self, message: telebot.types.Message):
        try:
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.remindePoll,
                message.chat.id,
            )

            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return

            # print(f'Message: {message.text}')
            command_parts = message.text.strip().split()
            if len(command_parts) < 2:
                self.bot.reply_to(
                    message,
                    "Jo, do muast jetzt scho dazuaschreiben wost willst. Probiers numoi",
                )
                return

            self.bot.set_state(
                message.from_user.id,
                LeistungsState.genericLeistungsmessage,
                message.chat.id,
            )

            self.bot.reply_to(
                message,
                "Wüst des auf irgend an poll replyen?",
                reply_markup=self.helper.open_polls_button(True),
            )

        except Exception as error:
            self.helper.report_error(message, error)

    def access_of(self, message) -> Commands.Access:
        """! How much of the command list `message`'s sender may see

        Mirrors the two checks the handlers themselves use. It only decides
        what `/help` prints - a sender who talks their way past this still
        meets the handler's own check.
        """
        if message.from_user.username in lc.config["usernames"]:
            return Commands.Access.OWNER
        try:
            if self.helper.sender_has_permission(message):
                return Commands.Access.ADMIN
        except Exception:
            # not reachable from this chat, or telegram said no - the
            # public list is the safe answer, not an error
            logging.debug("could not resolve admin status", exc_info=True)
        return Commands.Access.PUBLIC

    def publish_commands(self) -> None:
        """! Hands the command list to telegram, for the in-app menu

        Only the public commands: the menu is the same for everybody, so
        putting the admin ones in it would advertise commands most of the
        chat cannot run. They keep working when typed.

        Called from `main`, not from `__init__` - this is an api call, and a
        freshly constructed bot must stay usable without one.
        """
        try:
            self.bot.set_my_commands(
                Commands.as_telebot(
                    Commands.visible_to(Commands.Access.PUBLIC),
                ),
            )
        except Exception:
            # a bot that cannot publish its menu is still a working bot
            logging.warning("could not publish the commands", exc_info=True)

    def process_cancel(self, message, user_id: int | None = None) -> None:
        """! Ends whatever the sender was in the middle of

        @param message Where to answer, and whose author to clear by default
        @param user_id Who to clear instead, when that is not the author

        `user_id` has to be passed from a callback. The message an inline
        button sits on was sent by the bot, so its `from_user` is the bot's
        own account and clearing that state clears nothing - the button
        answered "Halt Stop." while leaving the presser exactly where they
        were. See #78.

        Also throws away whatever the workflow had pickled. A scratch file
        was only ever deleted by the button that consumed it, so cancelling
        a search or rejecting a preview used to leave one behind for good
        (#97).
        """
        self.bot.send_message(
            message.chat.id,
            "Halt Stop.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        if user_id is None:
            user_id = message.from_user.id
        self.bot.delete_state(user_id, message.chat.id)
        self.discard_scratch(user_id)

    def process_send_nudes(self, chat_id):
        self.helper.send_nude(chat_id)

    def process_generic_leistungsmessage(
        self,
        original_message: telebot.types.Message,
        leistungstag_id,
    ):
        command_parts = original_message.text.strip().split()
        msg = " ".join(command_parts[1:])

        if leistungstag_id is not None:
            leistungstag = self.helper.db.getLeistungstag(leistungstag_id)
            self.bot.send_message(
                lc.config["leistungschat_id"],
                msg,
                reply_to_message_id=leistungstag["poll_id"],
            )
        else:
            self.bot.send_message(lc.config["leistungschat_id"], msg)

        print(
            f'User {original_message.from_user.username} sent generic message "{msg}"',
        )

        self.bot.delete_state(
            original_message.from_user.id,
            original_message.chat.id,
        )
