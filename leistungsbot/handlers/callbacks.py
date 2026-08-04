# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The single entry point for every inline button the bot sends."""

from __future__ import annotations

import json
from datetime import datetime

from leistungsbot import leistungs_config as lc
from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.leistungs_returns import LeistungsReturnCodes
from leistungsbot.states import LeistungsState

#: The buttons only an administrator of the leistungschat may press.
#:
#: Mirrors `Commands.Access.ADMIN` on the command that offers the button:
#: everything reached from /leistungspoll, /purge, /closepoll, /sendreminder
#: or /message. The public flows - adding a location, the history, the
#: ratings, and the cancel button - are deliberately not in here.
#:
#: Written without the 🍻 prefix, `callback_query` strips it before matching.
ADMIN_CALLBACKS = frozenset(
    {
        "publish",
        "purge_type",
        "dry_purge",
        "purge",
        "open",
        # the "Nö" next to the open polls, /message's do-not-reply-to-a-poll
        "no",
        "closed",
        "poll_date",
        "open_hours_checked",
    },
)


class CallbackHandlers:
    """The single entry point for every inline button the bot sends."""

    def presser_has_permission(self, call) -> bool:
        """! Whether the person who pressed the button may go on

        The presser is `call.from_user`. `call.message` is the message the
        inline keyboard sits on, and the bot sent that one - handing it to
        `sender_has_permission` asks whether the *bot* is an administrator
        of the leistungschat. It is, in the usual setup, so that check said
        yes to everybody. See #99.

        Refuses out loud, so a button that does nothing does not look like a
        bot that is broken.
        """
        if self.helper.user_has_permission(call.from_user.id):
            return True
        self.bot.reply_to(
            call.message,
            "Diese Funktion ist nicht für den Pöbel gedacht.",
        )
        return False

    def unhandled_callback(self, call):
        """! Reports a button press nothing else claimed

        Registered last and without a filter, so it only sees what neither
        the calendar nor `Helper.filter` took - callback data that is not
        the bot's own `{"🍻cmd": value}` json.

        Until #82 `callback_query` was that catch-all by accident: its
        filter evaluated to `None` and telebot dropped it. Giving the filter
        back its `return` would have made a foreign callback disappear
        without a word, so the reporting moved here instead of going away.
        """
        try:
            self.bot.answer_callback_query(call.id, "Copy that")
            self.bot.send_message(
                lc.config["chat_id"],
                f"Hi Devs!!\nHandle this callback\n{call.data}",
            )
        except Exception as error:
            self.helper.report_error(call.message, error)

    def callback_query(self, call):
        try:
            data = json.loads(call.data)
            if len(data) == 0:
                self.bot.answer_callback_query(
                    call.id,
                    "SHHEEEEESH des hod ned funktioniert",
                )
                return
            cmd = [*data][0].replace("🍻", "")
            val = [*data.values()][0]
            self.bot.answer_callback_query(call.id, "Copy that")
            if cmd in ADMIN_CALLBACKS and not self.presser_has_permission(
                call,
            ):
                # the keyboard stays: somebody who may press it still can
                return
            if cmd == "search":
                self.helper.approve_location(
                    call.message.chat.id,
                    val[0],
                    val[1],
                )
            elif cmd == "select":
                if val[1] < 0:
                    if (self.helper.get_rand_len(val[0])) == 1:
                        self.bot.send_message(
                            call.message.chat.id,
                            "Daun füg a boa mehr infos zu deiner Suche dazua...",
                        )
                    else:
                        self.bot.send_message(
                            call.message.chat.id,
                            "Daun probiern mas numoi...",
                            reply_markup=self.helper.restore_search_location_button(
                                val[0],
                            ),
                        )
                else:
                    res = self.helper.add_location(val[0], val[1])
                    # add_location consumed the scratch file
                    self.forget_scratch(call, val[0])
                    if res == LeistungsReturnCodes.DB_DUPLICATE:
                        self.bot.send_message(
                            call.message.chat.id,
                            "Des isch scho drin, du deppata!",
                        )
            elif cmd == "cancel":
                # call.from_user, not call.message.from_user: the message
                # the button sits on was sent by the bot
                self.process_cancel(call.message, call.from_user.id)
            elif cmd == "publish":
                self.helper.publish_leistungstag(val)
                # publish_leistungstag consumed the scratch file
                self.forget_scratch(call, val)
                self.bot.send_message(
                    call.message.chat.id,
                    "Hauma so veröffentlicht",
                )
            elif cmd == "q":
                self.process_search_location(call, call.message.chat.id, val)
            elif cmd == "history_type":
                self.bot.send_message(
                    call.message.chat.id,
                    "Welchen Leistungstag willst da anschaun?",
                    reply_markup=self.helper.leistungstag_history_button(
                        LeistungsTyp(val),
                    ),
                )
            elif cmd == "purge_type":
                self.bot.send_message(
                    call.message.chat.id,
                    "Welchen Leistungstag willst löschen?",
                    reply_markup=self.helper.leistungstag_dry_purge_button(
                        LeistungsTyp(val),
                    ),
                )
            elif cmd == "history":
                self.helper.send_history_info(
                    call.message.chat.id,
                    val,
                )
            elif cmd == "dry_purge":
                self.helper.send_purge_info(
                    call.message.chat.id,
                    val,
                )
            elif cmd == "purge":
                if self.helper.purge_leistungstag(val):
                    self.bot.send_message(
                        call.message.chat.id,
                        "zack und weg ises",
                    )
                else:
                    self.bot.send_message(
                        call.message.chat.id,
                        "De Nachrichtn muast leida manuell löschen",
                    )
            elif cmd == "location":
                self.helper.send_location_info2(call.message.chat.id, val)
            elif cmd == "open":
                if (
                    self.bot.get_state(
                        call.from_user.id,
                        call.message.chat.id,
                    )
                    == LeistungsState.remindePoll.name
                ):
                    self.process_reminder(
                        call.message,
                        val,
                        call.from_user.id,
                    )
                elif (
                    self.bot.get_state(
                        call.from_user.id,
                        call.message.chat.id,
                    )
                    == LeistungsState.closePoll.name
                ):
                    self.process_closepoll(
                        call.message,
                        val,
                        user_id=call.from_user.id,
                    )
                elif (
                    self.bot.get_state(
                        call.from_user.id,
                        call.message.chat.id,
                    )
                    == LeistungsState.sneakyClosePoll.name
                ):
                    self.process_closepoll(
                        call.message,
                        val,
                        True,
                        user_id=call.from_user.id,
                    )
                elif (
                    self.bot.get_state(
                        call.from_user.id,
                        call.message.chat.id,
                    )
                    == LeistungsState.genericLeistungsmessage.name
                ):
                    self.process_generic_leistungsmessage(
                        call.message.reply_to_message,
                        val,
                    )
            elif cmd == "closed":
                self.bot.reply_to(
                    call.message,
                    "Der Poll is scho closed. Willst wirklich on den reminden?",
                    reply_markup=self.helper.confirm_leistungstag_button(
                        val,
                    ),
                )
            elif cmd == "no":
                self.process_generic_leistungsmessage(
                    call.message.reply_to_message,
                    val,
                )
            elif cmd == "poll_date":
                if val:
                    if not self.context_of(call).poller:
                        self.helper.bot.send_message(
                            call.message.chat_id,
                            "Da is wohl was schiefglaufen, i kann ka poll findn...",
                        )
                    else:
                        self.check_open_hours_before_sending(
                            call,
                            datetime.strptime(
                                val,
                                self.helper.dateformat,
                            ).date(),
                        )
                else:
                    self.helper.pick_date(call.message.chat.id)
            elif cmd == "open_hours_checked":
                self.process_check_open_hours(call, val)
            else:
                self.bot.send_message(
                    lc.config["chat_id"],
                    f"Hi Devs!!\nHandle this callback\n{cmd}",
                )
            self.bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception as error:
            self.helper.report_error(call.message, error)
