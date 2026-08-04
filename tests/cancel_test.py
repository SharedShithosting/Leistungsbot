# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/cancel, from every state the bot can be in. Closes #78.

`/cancel` is registered with `state="*"` and has to win against whichever
state handler is currently listening. Every state gets the same three
questions: is the state gone, was the keyboard taken away, and did anything
blow up on the way.

The states are read off `LeistungsState` rather than listed here, so a new
state arrives in this file the moment it is declared.
"""

from __future__ import annotations

import pytest
from telebot.handler_backends import State

from leistungsbot.states import LeistungsState
from tests import support

ALL_STATES = sorted(
    name
    for name, value in vars(LeistungsState).items()
    if isinstance(value, State)
)


def test_every_state_is_covered():
    """Guards the introspection above: a typo would silently test nothing."""
    assert len(ALL_STATES) >= 14
    assert "normalLocation" in ALL_STATES
    assert "switcherooAlternateLocation" in ALL_STATES


def enter(app, state_name: str) -> None:
    app.bot.set_state(
        support.ADMIN_USER_ID,
        getattr(LeistungsState, state_name),
        support.GROUP_CHAT_ID,
    )
    assert support.state_of(app) == f"LeistungsState:{state_name}"


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_cancel_clears_the_state(app, state_name):
    enter(app, state_name)

    support.send_command(app, "/cancel")

    assert support.state_of(app) is None


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_cancel_says_so(app, state_name):
    enter(app, state_name)

    support.send_command(app, "/cancel")

    support.assert_said(app, "Halt Stop.")


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_cancel_does_not_report_an_error(app, state_name):
    enter(app, state_name)

    support.send_command(app, "/cancel")

    support.assert_no_dev_error(app)


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_cancel_takes_the_keyboard_away(app, state_name):
    """A left over reply keyboard would keep offering a dead workflow."""
    enter(app, state_name)

    support.send_command(app, "/cancel")

    removals = [
        kwargs.get("reply_markup")
        for name, _, kwargs in app.outbox
        if name == "send_message" and kwargs.get("reply_markup") is not None
    ]
    assert any(
        type(markup).__name__ == "ReplyKeyboardRemove" for markup in removals
    )


def test_cancel_without_a_state_is_harmless(app):
    """#13, the last piece of it.

    Inside a conversation /cancel works - every test above proves it. What
    did nothing is /cancel on its own, which is how the command looks to
    anyone who types it speculatively: it was registered with `state="*"`,
    and telebot matches that only while a state is set.
    """
    assert support.state_of(app) is None

    support.send_command(app, "/cancel")

    support.assert_said(app, "Halt Stop.")
    support.assert_no_dev_error(app)


def test_cancel_without_a_state_leaves_it_that_way(app):
    assert support.state_of(app) is None

    support.send_command(app, "/cancel")

    assert support.state_of(app) is None


def test_cancel_without_a_state_takes_the_keyboard_away(app):
    """The reply keyboard outlives the conversation that put it there."""
    support.send_command(app, "/cancel")

    removals = [
        kwargs.get("reply_markup")
        for name, _, kwargs in app.outbox
        if name == "send_message" and kwargs.get("reply_markup") is not None
    ]
    assert any(
        type(markup).__name__ == "ReplyKeyboardRemove" for markup in removals
    )


def test_cancel_still_wins_against_the_state_handlers(app):
    """Dropping the state filter must not let a state handler eat /cancel.

    `/leistungspoll` listens for a location name; without the ordering
    below, /cancel would arrive there as one.
    """
    support.send_command(app, "/leistungspoll")
    assert support.state_of(app) == "LeistungsState:normalLocation"

    support.send_command(app, "/cancel")

    support.assert_said(app, "Halt Stop.")
    support.assert_not_said(app, "kenn i ned")
    assert support.state_of(app) is None


# --- the 🍻cancel buttons -----------------------------------------------
#
# Every "Na" / "Des mochn ma ned!" button sends the same payload. The
# message they sit on was sent by the bot, so the handler has to take the
# presser from the callback and not from the message it is attached to.


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_the_cancel_button_clears_the_pressers_state(app, state_name):
    enter(app, state_name)

    support.press(app, {"🍻cancel": None})

    assert support.state_of(app) is None


def test_the_cancel_button_says_so(app):
    enter(app, "searchLocation")

    support.press(app, {"🍻cancel": None})

    support.assert_said(app, "Halt Stop.")


def test_the_cancel_button_does_not_clear_somebody_else(app):
    other = 3003
    enter(app, "normalLocation")
    app.bot.set_state(
        other,
        LeistungsState.rateLocation,
        support.GROUP_CHAT_ID,
    )

    support.press(app, {"🍻cancel": None}, user_id=support.ADMIN_USER_ID)

    assert support.state_of(app) is None
    assert (
        support.state_of(app, user_id=other) == "LeistungsState:rateLocation"
    )


def test_the_cancel_button_from_an_unknown_location(app, db):
    """The case #78 reproduced by hand: /leistungspoll, a location the bot
    does not know, then "Na"."""
    db.getLocationInfo.side_effect = lambda name: None

    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Nicht Existent")
    assert support.state_of(app) == "LeistungsState:searchLocation"

    support.press(app, {"🍻cancel": None})

    assert support.state_of(app) is None


# --- typing it wrong ----------------------------------------------------


@pytest.mark.parametrize("state_name", ALL_STATES)
def test_the_misspelling_works_too(app, state_name):
    """`cancel` is how the code spells it internally, so it is the typo
    people make. It is an alias rather than swallowed as text input."""
    enter(app, state_name)

    support.send_command(app, "/cancel")

    assert support.state_of(app) is None
    support.assert_said(app, "Halt Stop.")


def test_an_unregistered_command_is_not_swallowed(app):
    support.send_command(app, "/leistungspoll")

    support.send_command(app, "/thisisnotacommand")

    said = " ".join(support.sent_texts(app))
    assert "kenn i ned" not in said, "taken as a location name"


def test_cancel_only_clears_the_sender(app):
    """One user cancelling must not drop somebody else's conversation."""
    other = 2002
    enter(app, "normalLocation")
    app.bot.set_state(
        other,
        LeistungsState.rateLocation,
        support.GROUP_CHAT_ID,
    )

    support.send_command(app, "/cancel")

    assert support.state_of(app) is None
    assert (
        support.state_of(app, user_id=other) == "LeistungsState:rateLocation"
    )
