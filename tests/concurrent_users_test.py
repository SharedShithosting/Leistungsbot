# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Two people using the bot at the same time.

`LeistungsBot.poller` used to be a single attribute for the whole bot, so
whoever started a poll last owned it and the other one silently continued
into someone else's workflow. That is #14. The state is per user now, and
these tests are what says so.
"""

from __future__ import annotations

from leistungsbot.BotHelper import LeistungsTyp
from tests import support

ANNA = 1001
BERT = 1002


def start_poll(app, command: str, location: str, user_id: int) -> None:
    support.send_command(app, command, user_id=user_id)
    support.send_command(app, location, user_id=user_id)


def test_two_polls_at_once_keep_their_own_location(app):
    start_poll(app, "/leistungspoll", "Bar A", ANNA)
    start_poll(app, "/konkurrenzpoll", "Bar B", BERT)

    support.assert_no_dev_error(app)
    assert support.poller_of(app, ANNA).location == "Bar A"
    assert support.poller_of(app, BERT).location == "Bar B"


def test_two_polls_at_once_keep_their_own_kind(app):
    start_poll(app, "/leistungspoll", "Bar A", ANNA)
    start_poll(app, "/konkurrenzpoll", "Bar B", BERT)

    assert support.poller_of(app, ANNA).type == LeistungsTyp.NORMAL
    assert support.poller_of(app, BERT).type == LeistungsTyp.KONKURENZ


def test_the_second_starter_does_not_reset_the_first(app):
    """The interleaving that used to lose Anna's poll entirely."""
    support.send_command(app, "/leistungspoll", user_id=ANNA)
    support.send_command(app, "/zusatzpoll", user_id=BERT)
    support.send_command(app, "Bar B", user_id=BERT)
    support.send_command(app, "Bar A", user_id=ANNA)

    support.assert_no_dev_error(app)
    assert support.poller_of(app, ANNA).location == "Bar A"
    assert support.poller_of(app, ANNA).type == LeistungsTyp.NORMAL
    assert support.poller_of(app, BERT).location == "Bar B"
    assert support.poller_of(app, BERT).type == LeistungsTyp.ZUSATZ


def test_a_user_without_a_workflow_gets_an_empty_context(app):
    message = support.make_message("/alive", user_id=ANNA)
    context = app.context_of(message)

    assert context.poller is None
    assert context.leistungstag is None


def test_the_context_is_the_same_object_on_every_lookup(app):
    message = support.make_message("/alive", user_id=ANNA)

    first = app.context_of(message)
    first.leistungstag = {"key": 7}

    assert app.context_of(message) is first
    assert app.context_of(message).leistungstag == {"key": 7}


def test_a_callback_finds_the_context_its_sender_built(app):
    """Callbacks carry `from_user` too, which is what keys the lookup."""
    start_poll(app, "/leistungspoll", "Bar A", ANNA)

    callback = support.make_callback({"🍻noop": None}, user_id=ANNA)

    assert app.context_of(callback).poller.location == "Bar A"
