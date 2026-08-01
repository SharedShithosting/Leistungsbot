# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/zusatzpoll - like /leistungspoll, but the date is always picked manually.

There is no "next tuesday" suggestion here, the calendar opens right away and
any weekday is fine.
"""
from __future__ import annotations

from datetime import date
from datetime import timedelta

from leistungsbot.BotHelper import LeistungsTyp
from tests import support


def next_weekday(weekday: int) -> date:
    """The next upcoming date with the given weekday (0 = monday)."""
    today = date.today()
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def test_pleb_is_rejected(pleb):
    support.send_command(pleb, "/zusatzpoll")

    support.assert_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) is None


def test_asks_for_a_location(app):
    support.send_command(app, "/zusatzpoll")

    support.assert_no_dev_error(app)
    assert support.state_of(app) == "LeistungsState:zusatzLocation"
    support.assert_said(app, "Schick de nexte location")


def test_location_opens_the_calendar_instead_of_a_suggestion(app):
    support.send_command(app, "/zusatzpoll")
    support.send_command(app, "Bar A")

    support.assert_no_dev_error(app)
    assert app.poller.type == LeistungsTyp.ZUSATZ
    assert app.poller.location == "Bar A"
    support.assert_said(app, "Select year")
    support.assert_not_said(app, "Für wann wollen ma pollen?")


def test_any_weekday_is_accepted(app):
    support.send_command(app, "/zusatzpoll")
    support.send_command(app, "Bar A")
    friday = next_weekday(4)

    support.pick_calendar_date(app, friday)

    support.assert_no_dev_error(app)
    support.assert_not_said(app, "Blasphemie")
    question = app.bot.send_poll.call_args.args[1]
    assert question == (
        f'Leistungstag Zusatztermin 42: am {friday.strftime("%d.%m.%Y")} in "Bar A"'
    )
    support.assert_said(app, "Woin ma des so veröffentlichen?")


def test_publishing_stores_a_zusatz_leistungstag(app, db):
    support.send_command(app, "/zusatzpoll")
    support.send_command(app, "Bar A")
    support.pick_calendar_date(app, next_weekday(4))
    token = support.callback_payloads(support.last_markup(app))[-1][
        "🍻publish"
    ]

    support.press(app, {"🍻publish": token})

    support.assert_no_dev_error(app)
    assert db.addLeistungsTag.call_args.args[4] == int(LeistungsTyp.ZUSATZ)
