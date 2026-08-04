# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Which callback query ends up in which handler. Closes #82.

Three handlers are registered, and telebot stops at the first one that
matches:

1. the calendar library's own, for its ``cbcal_...`` buttons
2. ``callback_query``, filtered to the bot's ``{"🍻cmd": value}`` json
3. ``unhandled_callback``, unfiltered, for whatever is left

``Helper.filter`` used to build its predicate and forget to return it.
Telebot strips a ``None`` filter, so (2) ran with no filter at all and was
the catch-all - which is why nobody noticed. These tests pin the three
apart, so putting the filter back cannot silently swallow anything.
"""

from __future__ import annotations

from datetime import date
from datetime import timedelta

from tests import support

DEV_REPORT = "Handle this callback"


def test_our_own_json_reaches_the_real_handler(app, db):
    support.press(app, {"🍻location": 1})

    support.assert_not_said(app, DEV_REPORT)
    assert db.getLocationInfoByKey.called


def test_an_unknown_command_of_ours_is_still_reported(app):
    """A 🍻 payload passes the filter, so the report stays where it was."""
    support.press(app, {"🍻nonsense": 1})

    support.assert_said(app, DEV_REPORT)


def test_a_foreign_payload_is_reported_rather_than_acted_on(app):
    """Same key the bot uses, without the 🍻 - it must not select a location."""
    support.press(app, {"select": [1, 0]})

    support.assert_said(app, DEV_REPORT)
    assert not app.db.addLocation.called


def test_callback_data_that_is_not_json_is_reported(app):
    support.press_raw(app, "not json at all")

    support.assert_said(app, DEV_REPORT)


def test_the_report_names_the_payload(app):
    support.press_raw(app, "not json at all")

    support.assert_said(app, "not json at all")


def test_a_foreign_payload_is_answered(app):
    """An unanswered callback query leaves a spinner on the button."""
    support.press_raw(app, "not json at all")

    assert app.bot.answer_callback_query.called


def test_the_calendar_still_gets_its_own_buttons(app, db):
    """The calendar handler is registered first and must keep winning.

    Its ``cbcal_...`` data is not json, so without it the press would land
    in ``unhandled_callback`` and be reported as a bug.
    """
    support.send_command(app, "/zusatzpoll")
    support.send_command(app, "Bar A")

    support.pick_calendar_date(app, date.today() + timedelta(days=8))

    support.assert_not_said(app, DEV_REPORT)
