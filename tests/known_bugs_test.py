# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Tests written from an open issue, kept once it is closed.

Each test says what the bot *should* do. While the bug is open it carries
`open_bug(...)` - an `xfail(strict=True)` naming the issue - so the suite
stays green until somebody fixes it and turns red the moment they do
without removing the marker. Fixing a bug here means deleting one marker,
not writing a test from scratch, and the test then guards the fix.

Everything below has had its marker removed. Do not add one without an
issue number.
"""

from __future__ import annotations

import pytest

from tests import support


def open_bug(number: int, what: str):
    return pytest.mark.xfail(strict=True, reason=f"#{number}: {what}")


# --- #82 Helper.filter() returns None ----------------------------------
#
# Fixed. The predicate is returned now, so the handler is registered with a
# filter rather than as the catch-all for every callback query.


def test_the_callback_filter_is_a_predicate(app):
    assert callable(app.helper.filter())


def test_the_callback_filter_accepts_our_own_callbacks(app):
    predicate = app.helper.filter()
    assert predicate(support.make_callback({"🍻open": 1}))


def test_the_callback_filter_rejects_foreign_callbacks(app):
    predicate = app.helper.filter()
    assert not predicate(support.make_callback({"something-else": 1}))


# --- #15 sendreminder / closepoll with no open poll --------------------
#
# Fixed. `sneaky_closepoll` is in the list because it asked the same
# question through the same empty keyboard, it was just never reported.

NEEDS_AN_OPEN_POLL = ["/sendreminder", "/closepoll", "/sneaky_closepoll"]


@pytest.mark.parametrize("command", NEEDS_AN_OPEN_POLL)
def test_no_open_poll_is_said_out_loud(app, db, command):
    db.getOpenLeistungsTag.return_value = []

    support.send_command(app, command)

    said = " ".join(support.sent_texts(app)).lower()
    assert "poll" in said
    assert any(word in said for word in ("kan", "kein", "ka ", "nix"))


@pytest.mark.parametrize("command", NEEDS_AN_OPEN_POLL)
def test_no_open_poll_sends_no_empty_keyboard(app, db, command):
    db.getOpenLeistungsTag.return_value = []

    support.send_command(app, command)

    markup = support.last_markup_or_none(app)
    if markup is not None:
        assert support.button_labels(markup), "sent an empty keyboard"


@pytest.mark.parametrize("command", NEEDS_AN_OPEN_POLL)
def test_no_open_poll_ends_the_conversation(app, db, command):
    """Nothing can answer the question, so leaving the state set would
    strand the next message in a handler waiting for a button press."""
    db.getOpenLeistungsTag.return_value = []

    support.send_command(app, command)

    assert support.state_of(app) is None


@pytest.mark.parametrize("command", NEEDS_AN_OPEN_POLL)
def test_no_open_poll_is_not_an_error(app, db, command):
    db.getOpenLeistungsTag.return_value = []

    support.send_command(app, command)

    support.assert_no_dev_error(app)


# --- #17 commands are swallowed while in a conversation ----------------


def test_a_command_in_a_state_reaches_its_handler(app):
    """#17's first half.

    Every command handler is registered ahead of every state handler, so a
    command still wins while a conversation is open. That ordering is the
    whole reason `MESSAGE_HANDLERS` is an explicit list; this test is what
    notices if someone shuffles it.
    """
    support.send_command(app, "/leistungspoll")
    assert support.state_of(app) == "LeistungsState:normalLocation"

    support.send_command(app, "/alive")

    support.assert_said(app, "Ready To Serve You")


@pytest.mark.parametrize("command", ["/switcheroo", "/version"])
def test_the_bottom_of_the_table_reaches_its_handler_too(app, command):
    """These two sat *below* the state handlers and were swallowed."""
    support.send_command(app, "/leistungspoll")

    support.send_command(app, command)

    support.assert_not_said(app, "kenn i ned")


def test_starting_another_command_leaves_the_first_state(app):
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "/history")

    assert support.state_of(app) != "LeistungsState:normalLocation"


def test_the_reply_after_two_commands_answers_the_second(app):
    """The bug as reported: /add_location, /show_locations, then a name.

    The name was read as the answer /add_location was waiting for, so the
    bot searched google for it as if the second command had not happened.
    """
    support.send_command(app, "/add_location")
    support.send_command(app, "/show_locations")

    support.send_command(app, "Some Unknown Bar")

    assert not app.google.findPlace.called


def test_an_unknown_command_is_answered(app):
    support.send_command(app, "/thisisnotacommand")

    support.assert_said(app, "/help")


def test_an_unknown_command_keeps_the_conversation(app):
    """A typo is the one message that clearly did not mean to start
    something new, so it must not drop a half finished workflow."""
    support.send_command(app, "/leistungspoll")

    support.send_command(app, "/thisisnotacommand")

    assert support.state_of(app) == "LeistungsState:normalLocation"


def test_a_command_addressed_at_the_bot_is_still_known(app):
    """Telegram writes /help@leistungsbot in a group with several bots."""
    support.send_command(app, "/alive@leistungsbot")

    support.assert_said(app, "Ready To Serve You")


def test_plain_text_is_not_mistaken_for_a_command(app):
    support.send_command(app, "/leistungspoll")

    support.send_command(app, "Bar A")

    support.assert_said(app, "Für wann wollen ma pollen?")


def test_a_button_whose_conversation_ended_says_so(app):
    """/closepoll puts the answer in the state; a later command ends it,
    and the keyboard from before is still on screen."""
    support.send_command(app, "/closepoll")
    support.send_command(app, "/alive")

    support.press(app, {"🍻open": 10})

    support.assert_said(app, "I waß nimma")
