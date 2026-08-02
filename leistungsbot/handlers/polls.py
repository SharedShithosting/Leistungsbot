# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Creating a leistungstag: pick a kind, a location and a date."""

from __future__ import annotations

import time
from datetime import date

from telegram_bot_calendar import LSTEP
from telegram_bot_calendar import DetailedTelegramCalendar

from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.BotHelper import PersistantLeistungsTagPoller
from leistungsbot.google_place import Openness
from leistungsbot.states import LeistungsState


class PollHandlers:
    """Creating a leistungstag: pick a kind, a location and a date."""

    def poll_now(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.normalLocation,
                message.chat.id,
            )
            self.bot.send_message(
                message.chat.id,
                "Schick de nexte location muaz",
                reply_markup=self.helper.location_keyboard(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def zusatz_poll(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.zusatzLocation,
                message.chat.id,
            )
            self.bot.send_message(
                message.chat.id,
                "Schick de nexte location muaz",
                reply_markup=self.helper.location_keyboard(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def konkurrenz_poll(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.konkurrenzLocation,
                message.chat.id,
            )
            self.bot.send_message(
                message.chat.id,
                "Schick de nexte location muaz",
                reply_markup=self.helper.location_keyboard(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def get_poll_location(self, message):
        try:
            location = self.process_poll_location(message)
            if location:
                self.context_of(message).poller = PersistantLeistungsTagPoller(
                    self.helper,
                    message.chat.id,
                    location,
                    LeistungsTyp.NORMAL,
                )
                self.helper.bot.reply_to(
                    message,
                    "Für wann wollen ma pollen?",
                    reply_markup=self.helper.date_suggester(),
                )
        except Exception as error:
            self.helper.report_error(message, error)

    def get_konkurrenz_location(self, message):
        try:
            location = self.process_poll_location(message)
            if location:
                self.context_of(message).poller = PersistantLeistungsTagPoller(
                    self.helper,
                    message.chat.id,
                    location,
                    LeistungsTyp.KONKURENZ,
                )
                self.helper.bot.reply_to(
                    message,
                    "Für wann wollen ma pollen?",
                    reply_markup=self.helper.date_suggester(),
                )
        except Exception as error:
            self.helper.report_error(message, error)

    def get_zusatz_location(self, message):
        try:
            location = self.process_poll_location(message)
            if location:
                self.context_of(message).poller = PersistantLeistungsTagPoller(
                    self.helper,
                    message.chat.id,
                    location,
                    LeistungsTyp.ZUSATZ,
                )
                self.helper.pick_date(message.chat.id)
        except Exception as error:
            self.helper.report_error(message, error)

    def cal(self, call):
        result, key, step = DetailedTelegramCalendar(
            min_date=date.today(),
        ).process(call.data)
        if not result and key:
            self.helper.bot.edit_message_text(
                f"Select {LSTEP[step]}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=key,
            )
        elif result:
            self.helper.bot.edit_message_text(
                f"You selected {result}",
                call.message.chat.id,
                call.message.message_id,
            )
            poller = self.context_of(call).poller
            if not poller:
                self.helper.bot.send_message(
                    call.message.chat_id,
                    "Da is wohl was schiefglaufen, i kann ka poll findn...",
                )
                return
            if (
                poller.type == LeistungsTyp.NORMAL
                or poller.type == LeistungsTyp.KONKURENZ
            ) and result.weekday() != 1:
                self.helper.bot.send_message(
                    call.message.chat.id,
                    "Blasphemie, des is ka Dienstag wast da du do ausgsuacht hast...alles auf eigene Gefahr!",
                )
                time.sleep(1)

            self.check_open_hours_before_sending(call, result)

    def process_poll_location(self, message):
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
        elif info["visited"]:
            self.bot.reply_to(
                message,
                "Do woan ma schomoi, i hoff du wast wost duast.",
            )
            self.bot.delete_state(message.from_user.id, message.chat.id)
            return location
        else:
            self.bot.delete_state(message.from_user.id, message.chat.id)
            return location
        return None

    def check_open_hours_before_sending(self, call, date: date):
        poller = self.context_of(call).poller
        open_state = self.helper.check_open_hours(poller.location, date)

        if open_state[0] == Openness.OPEN:
            poller.dry_send_with_date(date)
        else:
            poller.date = date

            if open_state[0] == Openness.CLOSED:
                self.bot.send_message(
                    call.message.chat.id,
                    "I glaub ned, dass de offn hom. Bist da sicha?\n\n"
                    + open_state[1],
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Des passt so, i kenn mi aus",
                    ),
                )
            elif open_state[0] == Openness.SHORT:
                self.bot.send_message(
                    call.message.chat.id,
                    "Is da des long gmua?\n\n" + open_state[1],
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Jo, passt scho",
                    ),
                )
            elif open_state[0] == Openness.UNKNOWN:
                self.bot.send_message(
                    call.message.chat.id,
                    "I was jetzt hod ned, ob de offen hom. Muast söwa schaun.",
                    reply_markup=self.helper.check_open_hours_keyboard(
                        "Des passt so, i kenn mi aus",
                        "Schaut schlecht aus",
                    ),
                )

    def process_check_open_hours(self, callback, open_hours_correct):
        if open_hours_correct:
            self.context_of(callback).poller.dry_send()
