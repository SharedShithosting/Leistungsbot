# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/message - let the bot say something in the leistungschat.

    /message <text> -> pick a poll to reply to (or "Nö") -> leistungschat
"""
from __future__ import annotations

from tests import support
from tests.fixtures import make_leistungstag
from tests.fixtures import POLL_MESSAGE_ID

COMMAND = "/message Heit gemma auf a Bier"
TEXT = "Heit gemma auf a Bier"


def ask(app, command: str = COMMAND) -> dict:
    """Send the command; returns the payload of the original message."""
    payload = support.message_payload(command)
    support.send(app, support.make_message(command))
    return payload


def test_pleb_is_rejected(pleb):
    ask(pleb)

    support.assert_said(pleb, "nicht für den Pöbel")
    assert pleb.bot.send_message.call_count == 0


def test_message_without_text_is_refused(app):
    ask(app, "/message")

    support.assert_no_dev_error(app)
    support.assert_said(app, "do muast jetzt scho dazuaschreiben wost willst")
    assert support.state_of(app) != "LeistungsState:genericLeistungsmessage"


def test_asks_which_poll_to_reply_to(app, db):
    db.getOpenLeistungsTag.return_value = [make_leistungstag(key=10)]

    ask(app)

    support.assert_no_dev_error(app)
    assert support.state_of(app) == "LeistungsState:genericLeistungsmessage"
    support.assert_said(app, "Wüst des auf irgend an poll replyen?")
    assert support.callback_payloads(support.last_markup(app)) == [
        {"🍻open": 10},
        {"🍻no": None},
    ]


def test_replying_to_a_poll(app, db):
    original = ask(app)

    support.press(app, {"🍻open": 10}, reply_to_message=original)

    support.assert_no_dev_error(app)
    db.getLeistungstag.assert_called_with(10)
    sent = app.bot.send_message.call_args
    assert sent.args[0] == support.LEISTUNGSCHAT_ID
    assert sent.args[1] == TEXT
    assert sent.kwargs["reply_to_message_id"] == POLL_MESSAGE_ID
    assert support.state_of(app) is None


def test_sending_without_a_poll(app):
    original = ask(app)

    support.press(app, {"🍻no": None}, reply_to_message=original)

    support.assert_no_dev_error(app)
    sent = app.bot.send_message.call_args
    assert sent.args[0] == support.LEISTUNGSCHAT_ID
    assert sent.args[1] == TEXT
    assert "reply_to_message_id" not in sent.kwargs
    assert support.state_of(app) is None


def test_the_command_itself_is_stripped(app):
    original = ask(app, "/message  mehrere   wörter  ")

    support.press(app, {"🍻no": None}, reply_to_message=original)

    support.assert_no_dev_error(app)
    assert app.bot.send_message.call_args.args[1] == "mehrere wörter"


def test_nothing_is_sent_before_the_poll_is_chosen(app):
    ask(app)

    support.assert_no_dev_error(app)
    leistungschat_calls = [
        args
        for name, args, _ in app.outbox
        if name == "send_message"
        and args
        and args[0] == support.LEISTUNGSCHAT_ID
    ]
    assert leistungschat_calls == []
