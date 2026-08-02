# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/sendreminder, and the /purge preamble.

/sendreminder takes an optional date: without one it offers the open polls,
with one it looks that day up. The date branch was the largest uncovered
piece of the lifecycle handlers.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta

import pytest

from leistungsbot.states import LeistungsState
from tests import support
from tests.fixtures import POLL_MESSAGE_ID
from tests.fixtures import make_leistungstag

TOMORROW = (datetime.now() + timedelta(days=1)).date()
YESTERDAY = (datetime.now() - timedelta(days=1)).date()


def remind(app, argument: str = "") -> None:
    command = "/sendreminder" + (f" {argument}" if argument else "")
    support.send_command(app, command)


# --- without a date -----------------------------------------------------


def test_the_bare_command_offers_the_open_polls(app, db):
    db.getOpenLeistungsTag.return_value = [make_leistungstag()]

    remind(app)

    support.assert_said(app, "An welchen Poll wüst reminden?")
    support.assert_no_dev_error(app)


def test_the_bare_command_is_refused_to_a_pleb(pleb):
    remind(pleb)

    support.assert_said(pleb, "nicht für den Pöbel")


# --- with a date --------------------------------------------------------


def test_a_date_in_the_past_is_refused(app):
    remind(app, YESTERDAY.isoformat())

    support.assert_said(app, "zu spät zum reminden")


def test_something_that_is_not_a_date_is_explained(app):
    remind(app, "morgen bitte")

    support.assert_said(app, "Soi des a Datum sei?")
    support.assert_no_dev_error(app)


def test_a_day_without_a_leistungstag_says_so(app, db):
    db.getLeistungstageByDate.return_value = None

    remind(app, TOMORROW.isoformat())

    support.assert_said(app, "ka Leistungstog")


def test_one_open_leistungstag_asks_for_confirmation(app, db):
    db.getLeistungstageByDate.return_value = [
        make_leistungstag(date=TOMORROW, closed=0),
    ]

    remind(app, TOMORROW.isoformat())

    support.assert_said(app, "Willst on den reminden?")
    assert support.button_labels(support.last_markup(app)) == ["Na", "Jo"]


def test_one_closed_leistungstag_warns_first(app, db):
    db.getLeistungstageByDate.return_value = [
        make_leistungstag(date=TOMORROW, closed=1),
    ]

    remind(app, TOMORROW.isoformat())

    support.assert_said(app, "Poll is scho geclosed")


def test_the_location_is_named(app, db):
    db.getLeistungstageByDate.return_value = [
        make_leistungstag(date=TOMORROW, closed=0),
    ]

    remind(app, TOMORROW.isoformat())

    support.assert_said(app, "Bar A")


def test_several_leistungstage_on_one_day_are_offered_as_a_list(app, db):
    db.getLeistungstageByDate.return_value = [
        make_leistungstag(key=1, date=TOMORROW, closed=0),
        make_leistungstag(key=2, date=TOMORROW, closed=0, location=2),
    ]

    remind(app, TOMORROW.isoformat())

    support.assert_said(app, "sogor mehrere Leistungstoge")
    assert len(support.button_labels(support.last_markup(app))) == 2


# --- confirming a reminder ----------------------------------------------


def test_confirming_sends_the_reminder(app, db):
    """The 🍻open button only acts while the sender is in remindePoll, so the
    command has to come first."""
    db.getOpenLeistungsTag.return_value = [make_leistungstag()]
    db.getLeistungstag.return_value = make_leistungstag()
    remind(app)

    support.press(app, {"🍻open": 1})

    support.assert_no_dev_error(app)
    support.assert_said(app, "Da Reminder is draußen!")


def test_the_reminder_replies_to_the_poll(app, db):
    db.getOpenLeistungsTag.return_value = [make_leistungstag()]
    db.getLeistungstag.return_value = make_leistungstag()
    remind(app)

    support.press(app, {"🍻open": 1})

    replies = [
        kwargs["reply_to_message_id"]
        for name, _, kwargs in app.outbox
        if name == "send_message" and "reply_to_message_id" in kwargs
    ]
    assert POLL_MESSAGE_ID in replies


def test_a_pleb_cannot_confirm_a_reminder(pleb, db):
    db.getOpenLeistungsTag.return_value = [make_leistungstag()]
    pleb.bot.set_state(
        support.ADMIN_USER_ID,
        LeistungsState.remindePoll,
        support.GROUP_CHAT_ID,
    )

    support.press(pleb, {"🍻open": 1})

    support.assert_said(pleb, "nicht für den Pöbel")


def test_saying_no_does_not_send_a_reminder(app, db):
    db.getLeistungstag.return_value = make_leistungstag()

    support.press(app, {"🍻cancle": None})

    support.assert_said(app, "Halt Stop.")


# --- /purge -------------------------------------------------------------


def test_purge_is_refused_to_a_pleb(pleb):
    support.send_command(pleb, "/purge")

    support.assert_said(pleb, "nicht für den Pöbel")


def test_purge_asks_which_kind(app):
    support.send_command(app, "/purge")

    assert app.bot.send_animation.called
    caption = app.bot.send_animation.call_args.kwargs["caption"]
    assert "löschen" in caption


@pytest.mark.parametrize("closed", [0, 1])
def test_purge_offers_the_leistungstage(app, db, closed):
    db.getLeistungsTags.return_value = [make_leistungstag(closed=closed)]

    support.send_command(app, "/purge")
    support.press(app, {"🍻purge_type": 1})

    support.assert_no_dev_error(app)
