# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The list of places a leistungstag can go."""

from __future__ import annotations

from datetime import datetime

from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.states import LeistungsState


class LocationHandlers:
    """The list of places a leistungstag can go."""

    def add_location(self, message):
        try:
            self.bot.set_state(
                message.from_user.id,
                LeistungsState.searchLocation,
                message.chat.id,
            )
            self.bot.send_message(
                message.chat.id,
                "Schick dei location idee muaz",
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def remove_location_handler(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return

            self.bot.set_state(
                message.from_user.id,
                LeistungsState.removeLocation,
                message.chat.id,
            )
            self.bot.reply_to(
                message,
                "Welche Location willst löschen?",
                reply_markup=self.helper.location_keyboard(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def remove_location(self, message):
        try:
            self.helper.remove_location(message.text)
            self.bot.reply_to(message, "Hab de location murz destroyed!")
        except Exception as error:
            self.helper.report_error(message, error)

    def search_location(self, message):
        try:
            self.process_search_location(
                message,
                message.chat.id,
                message.text.strip(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def rate_location_handler(self, message):
        try:
            if message.chat.type != "private":
                self.helper.bot.reply_to(
                    message,
                    "Und wenn ma des ned im Gruppenchat machen, du Bauernschädl?",
                )
            else:
                leistungstag = self.helper.db.getLeistungsTags(
                    LeistungsTyp.NORMAL,
                    max_results=1,
                    before=datetime.now(),
                )[0]
                self.helper.send_location_info2(
                    message.chat.id,
                    leistungstag["location"],
                )
                self.helper.bot.send_message(
                    message.chat.id,
                    "Wiafü Monde wüst erm geben?",
                    reply_markup=self.helper.rating_keyboard(),
                )
                self.bot.set_state(
                    message.from_user.id,
                    LeistungsState.rateLocation,
                    message.chat.id,
                )
        except Exception as error:
            self.helper.report_error(message, error)

    def rate_location(self, message):
        try:
            rating = self.helper.get_rating(message.text)
            leistungstag = self.helper.db.getLeistungsTags(
                LeistungsTyp.NORMAL,
                max_results=1,
                before=datetime.now(),
            )[0]
            self.helper.db.addUser(message.from_user.id, message.chat.id)
            try:
                self.helper.db.rateLocationKey(
                    leistungstag["location"],
                    message.from_user.id,
                    rating,
                )
            except BaseException:
                self.bot.send_message(
                    message.chat.id,
                    "WAHLBETRUG!! Du host schomoi obgstimmt.",
                )
            self.bot.delete_state(message.from_user.id)
        except Exception as error:
            self.helper.report_error(message, error)

    def show_locations(self, message):
        try:
            self.bot.reply_to(
                message,
                "Des san de nächsten Locations",
                reply_markup=self.helper.virgine_location_button(),
            )
        except Exception as error:
            self.helper.report_error(message, error)

    def process_search_location(self, update, chat_id, query):
        """! Runs a google search and offers what came back

        @param update The message or button press that asked for the search,
                      so the pickled results can be filed under whoever will
                      have to be cleaned up after (#97)
        @param chat_id Where to answer
        @param query What to look for
        """
        finds, rand_id = self.helper.search_location(query)
        self.remember_scratch(update, rand_id)
        if finds < 1:
            # nothing to pick from, so nothing will ever consume the pickle
            self.helper.discard_rand_file(rand_id)
            self.forget_scratch(update, rand_id)
            self.bot.send_message(
                chat_id,
                f'Wenn i nach "{query}" suach find i nix...vielleicht verschriebn?',
            )
        elif finds == 1:
            self.helper.approve_location(chat_id, rand_id, 0)
        elif finds > 1:
            self.bot.send_message(
                chat_id,
                "Suach da aus wost willst, oda schick ma wos aunders",
                reply_markup=self.helper.search_location_button(rand_id),
            )
