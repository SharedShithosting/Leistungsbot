# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/closepoll and /sneaky_closepoll - end the voting for a leistungstag.

Both pick an open poll from a button list; the sneaky variant does the same
thing but tells nobody in the leistungschat.
"""

from __future__ import annotations

import pytest

from tests import support
from tests.fixtures import POLL_MESSAGE_ID
from tests.fixtures import make_leistungstag

OPEN_KEY = 10
PUBLIC_CLOSE_MESSAGE = "Schluss, aus, vorbei"


@pytest.fixture(params=["/closepoll", "/sneaky_closepoll"])
def close_command(request) -> str:
    return request.param


def test_pleb_is_rejected(pleb, close_command):
    support.send_command(pleb, close_command)

    support.assert_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) is None


def test_offers_the_open_polls(app, db, close_command):
    db.getOpenLeistungsTag.return_value = [
        make_leistungstag(key=10, location=1),
        make_leistungstag(key=11, location=2),
    ]

    support.send_command(app, close_command)

    support.assert_no_dev_error(app)
    support.assert_said(app, "wüst")
    assert support.button_labels(support.last_markup(app)) == [
        "Bar A",
        "Bar B",
    ]
    assert support.callback_payloads(support.last_markup(app)) == [
        {"🍻open": 10},
        {"🍻open": 11},
    ]


def test_states_of_the_two_variants_differ(app):
    support.send_command(app, "/closepoll")
    assert support.state_of(app) == "LeistungsState:closePoll"

    support.send_command(app, "/sneaky_closepoll")
    assert support.state_of(app) == "LeistungsState:sneakyClosePoll"


def test_closing_stops_and_unpins_the_poll(app, db, close_command):
    support.send_command(app, close_command)

    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    db.closeLeistungstag.assert_called_once_with(OPEN_KEY)
    app.bot.stop_poll.assert_called_once_with(
        support.LEISTUNGSCHAT_ID,
        POLL_MESSAGE_ID,
    )
    app.bot.unpin_chat_message.assert_called_once_with(
        support.LEISTUNGSCHAT_ID,
        POLL_MESSAGE_ID,
    )
    support.assert_said(app, "De Poll is zua")


def test_closepoll_announces_it_in_the_leistungschat(app):
    support.send_command(app, "/closepoll")

    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    support.assert_said(app, PUBLIC_CLOSE_MESSAGE)
    announcement = next(
        (name, args, kwargs)
        for name, args, kwargs in app.outbox
        if name == "send_message" and PUBLIC_CLOSE_MESSAGE in str(args)
    )
    assert announcement[1][0] == support.LEISTUNGSCHAT_ID
    assert announcement[2]["reply_to_message_id"] == POLL_MESSAGE_ID
    app.bot.send_animation.assert_not_called()


def test_sneaky_closepoll_stays_quiet(app):
    support.send_command(app, "/sneaky_closepoll")

    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    support.assert_not_said(app, PUBLIC_CLOSE_MESSAGE)
    app.bot.send_animation.assert_called_once()
    assert (
        "De Poll is zua" in app.bot.send_animation.call_args.kwargs["caption"]
    )


def test_telegram_refusing_to_stop_the_poll_is_survived(app, db):
    """An already stopped poll must not abort the close."""
    app.bot.stop_poll.side_effect = RuntimeError("poll already closed")
    app.bot.unpin_chat_message.side_effect = RuntimeError("not pinned")
    support.send_command(app, "/closepoll")

    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    db.closeLeistungstag.assert_called_once_with(OPEN_KEY)
    support.assert_said(app, PUBLIC_CLOSE_MESSAGE)


def test_an_already_closed_poll_asks_for_confirmation(app, db):
    db.getOpenLeistungsTag.return_value = [make_leistungstag(key=12, closed=1)]
    support.send_command(app, "/closepoll")
    payload = support.callback_payloads(support.last_markup(app))[0]
    assert payload == {"🍻closed": 12}

    support.press(app, payload)

    support.assert_no_dev_error(app)
    support.assert_said(app, "Der Poll is scho closed")
    db.closeLeistungstag.assert_not_called()


def test_the_admin_of_an_instance_can_close_a_poll(app, db, close_command):
    """#9, end to end: the bot was never promoted in the leistungschat.

    The whole command, not just the button - this is what the reporter did
    on their own instance and got "nicht für den Pöbel" for. The check was
    handed the message the button sits on, which the bot sent, so it asked
    about the bot: not an admin there, refused everybody. See #99.
    """
    app.plebs.add(support.BOT_USER_ID)

    support.send_command(app, close_command)
    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    support.assert_not_said(app, "nicht für den Pöbel")
    db.closeLeistungstag.assert_called_once_with(OPEN_KEY)


def test_a_press_without_state_does_nothing(app, db):
    """The 🍻open button is shared by reminder, close and message."""
    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_no_dev_error(app)
    db.closeLeistungstag.assert_not_called()
    app.bot.stop_poll.assert_not_called()
