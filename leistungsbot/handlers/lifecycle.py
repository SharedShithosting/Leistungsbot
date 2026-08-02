# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""What happens to a leistungstag after it has been published."""

from __future__ import annotations

from datetime import date
from datetime import datetime

import telebot

from leistungsbot import assets
from leistungsbot import leistungs_config as lc
from leistungsbot.states import LeistungsState


class PollLifecycleHandlers:
    """What happens to a leistungstag after it has been published."""

    def send_reminder(self, message: telebot.types.Message):
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

            if len(command_parts) == 1:
                self.bot.reply_to(
                    message,
                    "An welchen Poll wüst reminden?",
                    reply_markup=self.helper.open_polls_button(),
                )
                return
            else:
                target_date_str = command_parts[1]

                try:
                    target_date = date.fromisoformat(target_date_str)
                except BaseException:
                    target_date = None
                    self.bot.send_message(
                        message.chat.id,
                        f"Soi des a Datum sei? Schick ma wonn donn sowos wie {datetime.now().date().isoformat()}",
                    )
                    self.bot.reply_to(
                        message,
                        "An welchen Poll wüst reminden?",
                        reply_markup=self.helper.open_polls_button(),
                    )

                # print(f'Date: {target_date}')

                if target_date is not None:
                    successful = (
                        self.try_remind_to_leistungstag_on_a_specific_date(
                            message,
                            target_date,
                        )
                    )
                    if not successful:
                        self.bot.reply_to(
                            message,
                            "An welchen Poll wüst reminden?",
                            reply_markup=self.helper.open_polls_button(),
                        )

        except Exception as error:
            self.bot.delete_state(message.from_user.id, message.chat.id)

            self.helper.report_error(message, error)

    def close_poll(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return

            self.bot.set_state(
                message.from_user.id,
                LeistungsState.closePoll,
                message.chat.id,
            )
            self.bot.reply_to(
                message,
                "Welchen Poll wüst closen?",
                reply_markup=self.helper.open_polls_button(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def sneaky_close_poll(self, message: telebot.types.Message) -> None:
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return

            self.bot.set_state(
                message.from_user.id,
                LeistungsState.sneakyClosePoll,
                message.chat.id,
            )
            self.bot.reply_to(
                message,
                "Welchen Poll wüst sneaky closen?",
                reply_markup=self.helper.open_polls_button(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def purge(self, message):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message,
                "Diese Funktion ist nicht für den Pöbel gedacht.",
            )
            return
        try:
            self.process_purge(message)
        except IndexError:
            return self.bot.reply_to(
                message,
                f"""Lol!!! An error in the wild:
                {message.text}

                Which is invalid.
                For more help use: /help
                """,
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def switcheroo(self, message: telebot.types.Message) -> None:
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message,
                "Diese Funktion ist nicht für den Pöbel gedacht.",
            )
            return

        self.bot.send_message(
            message.chat.id,
            "Wechan muastn ändern? Schick ma de nummer und i schau wos i doan konn.",
        )
        self.bot.set_state(
            message.from_user.id,
            LeistungsState.switcherooLeistungstagNumber,
            message.chat.id,
        )

    def switcheroo_leistungstag_number(
        self,
        message: telebot.types.Message,
    ) -> None:
        try:
            lt_number = int(message.text)
        except BaseException:
            self.bot.send_message(
                message.chat.id,
                "Host du in da Voikschui ned aufpasst wos a nummer is? Probiers numoi ...",
            )
            return

        lt = self.helper.db.getLeistungstagByNumber(lt_number)
        if lt is None:
            self.bot.send_message(
                message.chat.id,
                "Den Leistungstog find i ned. Schau numoi genau",
            )
            return

        print(f'Location {lt["location"]}')

        self.context_of(message).leistungstag = lt

        self.bot.send_message(
            message.chat.id,
            "Passt. Wo schau ma stottdessen hin?",
            reply_markup=self.helper.location_keyboard(),
        )
        self.bot.set_state(
            message.from_user.id,
            LeistungsState.switcherooAlternateLocation,
            message.chat.id,
        )

    def switcheroo_alternate_location(
        self,
        message: telebot.types.Message,
    ) -> None:
        context = self.context_of(message)
        if context.leistungstag is None:
            self.bot.send_message(
                message.chat.id,
                "Could not find Leistungstag in UserContext. This should not happen, please try again ...",
            )
            self.bot.delete_state(message.from_user.id, message.chat.id)
            return

        location = message.text.strip()
        # check if location exists in database
        info = self.helper.db.getLocationInfo(location)

        if not info:
            self.bot.send_message(
                message.chat.id,
                f"'{location}' kenn i ned..wüstas stattdessn zur listn dazua gebn?",
                reply_markup=self.helper.unkown_location_button(location),
            )
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.searchLocation,
                message.chat.id,
            )

        else:
            lt = context.leistungstag
            self.helper.db.switchLeistungstagLocation(
                lt["key"],
                lt["location"],
                info["key"],
            )

            self.bot.send_message(
                message.from_user.id,
                f"Ok, donn gemma am {lt['date'].strftime('%d.%m.%Y')} ins {info['name']}",
            )
            self.bot.delete_state(message.from_user.id, message.chat.id)

        context.leistungstag = None

    def process_reminder(self, message, leistungstag_key):
        if not self.helper.sender_has_permission(message):
            self.bot.reply_to(
                message,
                "Diese Funktion ist nicht für den Pöbel gedacht.",
            )
            return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.bot.send_message(
            lc.config["leistungschat_id"],
            "Reminder. Morgen wird reserviert. Letzte Chance zum Abstimmen 🗳️",
            reply_to_message_id=leistungstag["poll_id"],
        )
        self.bot.send_message(message.chat.id, "Da Reminder is draußen!")

    def process_closepoll(
        self,
        message: telebot.types.Message,
        leistungstag_key: int,
        sneaky: bool = False,
    ) -> None:
        # Check does not work when in callback
        # if not self.helper.sender_has_permission(message):
        #     self.bot.reply_to(
        #         message,
        #         "Diese Funktion ist nicht für den Pöbel gedacht.",
        #     )
        #     return

        leistungstag = self.helper.db.getLeistungstag(leistungstag_key)
        self.helper.db.closeLeistungstag(leistungstag_key)
        try:
            self.bot.stop_poll(
                lc.config["leistungschat_id"],
                leistungstag["poll_id"],
            )
        except BaseException:
            pass
        try:
            self.bot.unpin_chat_message(
                lc.config["leistungschat_id"],
                leistungstag["poll_id"],
            )
        except BaseException:
            pass
        if not sneaky:
            self.bot.send_message(
                lc.config["leistungschat_id"],
                "Schluss, aus, vorbei die Wahl is glaufen und für de de abgstimmt haben is a Platzerl reserviert.",
                reply_to_message_id=leistungstag["poll_id"],
            )
            self.bot.send_message(
                message.chat.id,
                "De Poll is zua. I hoff für dich d Reservierung is scho erledigt!",
            )
        else:
            with assets.gif("sneaky.gif") as sneakiely:
                self.bot.send_animation(
                    message.chat.id,
                    animation=telebot.types.InputFile(sneakiely),
                    caption="De Poll is zua. I hoff für dich d Reservierung is scho erledigt!",
                )

    def process_purge(self, message):
        with assets.gif("responisibility.gif") as responisibility:
            self.bot.send_animation(
                message.chat.id,
                telebot.types.InputFile(responisibility),
                caption="Welche Art von Leistungstag willst löschen?",
                reply_markup=self.helper.leistungstag_purge_type_button(),
            )

    def try_remind_to_leistungstag_on_a_specific_date(
        self,
        message: telebot.types.Message,
        target_date: date,
    ) -> bool:
        """! Reminds to polls of leistungstag on a specific date

        @param message Reminder command message
        @param target_date Date of the Leistungstag(e)

        @returns If Leistungstage on this date where found
        """

        if target_date < datetime.now().date():
            self.bot.send_message(
                message.chat.id,
                "Für des is zu spät zum reminden. Suach da wos ondares aus ...",
            )
            return False

        leistungstage = self.helper.db.getLeistungstageByDate(target_date)
        # print(f'Leistungstage: {leistungstage}')

        if leistungstage is None:
            self.bot.send_message(
                message.chat.id,
                "An dem Tog is ka Leistungstog. Suach da wos ondares aus ...",
            )
            return False

        if len(leistungstage) == 1:
            leistunstag = leistungstage[0]
            location_name = self.helper.db.getLocationName(
                leistunstag["location"],
            )

            if leistunstag["closed"] == 1:
                self.bot.reply_to(
                    message,
                    f"Leistungstag an dem Tog is bei {location_name}, aber da Poll is scho geclosed. Willst wirklich on den reminden?",
                    reply_markup=self.helper.confirm_leistungstag_button(
                        leistunstag["key"],
                    ),
                )
            else:
                self.bot.reply_to(
                    message,
                    f"Leistungstag an dem Tog is bei {location_name}. Willst on den reminden?",
                    reply_markup=self.helper.confirm_leistungstag_button(
                        leistunstag["key"],
                    ),
                )

        else:
            self.bot.send_message(
                message.chat.id,
                "Ein wöd Tog. Do san sogor mehrere Leistungstoge!",
            )
            self.bot.reply_to(
                message,
                "An welchen Poll wüst reminden?",
                reply_markup=self.helper.polls_button(leistungstage),
            )

        return True
