# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Looking back at the leistungstage that already happened."""

from __future__ import annotations


class HistoryHandlers:
    """Looking back at the leistungstage that already happened."""

    def history(self, message):
        try:
            self.process_history(message)
        except Exception as error:
            self.helper.report_error(message, error)

    def process_history(self, message):
        self.bot.send_message(
            message.chat.id,
            "Welche Art von Leistungstag willst da anschaun?",
            reply_markup=self.helper.leistungstag_history_type_button(),
        )
