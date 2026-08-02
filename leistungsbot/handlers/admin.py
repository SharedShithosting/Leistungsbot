# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Maintenance commands, for whoever runs the bot."""

from __future__ import annotations

from leistungsbot import leistungs_config as lc


class AdminHandlers:
    """Maintenance commands, for whoever runs the bot."""

    def showIds(self, message):
        try:
            if message.from_user.username in lc.config["usernames"]:
                file = open("joined_groups.txt", "r ")
                self.bot.send_document(message.chat.id, file)
                file.close()

        except Exception as error:
            self.bot.send_message(lc.config["chat_id"], str(error))

    def stats(self, message):
        try:
            if message.from_user.username in lc.config["usernames"]:
                print("Sending Stats To Owner")
                with open("joined_groups.txt") as file:
                    group_ids = []
                    for line in file.readlines():
                        for group_id in line.split(" "):
                            group_ids.append(group_id)
                            no_of_polls = len(group_ids)
                            no_of_groups = len(list(set(group_ids)))
                    group_ids.clear()
                    self.bot.reply_to(
                        message,
                        f"Number of polls Made: {no_of_polls}\n#Nr of groups bot has been added to: {no_of_groups}",
                    )
                    file.close()
            else:
                self.bot.reply_to(
                    message,
                    f"Sorry {message.from_user.username}! You Are Not Allowed To Use This Command,",
                )
        except Exception as error:
            try:
                group_ids.clear()
            except BaseException:
                pass
            self.helper.report_error(message, error)

    def ViewTheLogsFile(self, message):
        try:
            if message.from_user.username in lc.config["usernames"]:
                print("Owner Asked For The Logs!")
                file = open("POLL_LOGS.txt")
                self.bot.send_document(
                    message.chat.id,
                    file,
                    timeout=60,
                    disable_notification=True,
                )
                file.close()
                print("Logs Sent To Owner")
            else:
                self.bot.reply_to(
                    message,
                    f"Sorry {message.from_user.username}! You Are Not Allowed For This Command.",
                )
        except Exception as error:
            self.bot.reply_to(message, f"Error: {error}")

    def backup(self, message):
        try:
            if not self.helper.sender_has_permission(message):
                self.bot.reply_to(
                    message,
                    "Diese Funktion ist nicht für den Pöbel gedacht.",
                )
                return

            self.bot.reply_to(message, "I grab da de Datenbank zaum ...")
            self.helper.send_backup(message.chat.id)
        except Exception as error:
            self.helper.report_error(message, error)
