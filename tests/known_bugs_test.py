# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Tests for bugs that are still open.

Each test says what the bot *should* do and is marked `xfail(strict=True)`,
so the suite stays green while the bug is open and turns red the moment
somebody fixes it without removing the marker. Fixing a bug here means
deleting one `xfail` line, not writing a test from scratch.

The issue number is in every marker. Do not add an xfail here without one.
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
    """Not a bug any more - #17's first half.

    Every command handler is registered ahead of every state handler, so a
    command still wins while a conversation is open. That ordering is the
    whole reason `MESSAGE_HANDLERS` is an explicit list; this test is what
    notices if someone shuffles it.
    """
    support.send_command(app, "/leistungspoll")
    assert support.state_of(app) == "LeistungsState:normalLocation"

    support.send_command(app, "/alive")

    support.assert_said(app, "Ready To Serve You")


@open_bug(17, "the state survives a command that started something else")
def test_starting_another_command_leaves_the_first_state(app):
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "/history")

    assert support.state_of(app) != "LeistungsState:normalLocation"
