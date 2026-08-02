# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/konkurrenzpoll - same flow as /leistungspoll, different type and wording."""
from __future__ import annotations

from leistungsbot.BotHelper import LeistungsTyp
from tests import support
from tests.zusatzpoll_test import next_weekday


def test_pleb_is_rejected(pleb):
    support.send_command(pleb, "/konkurrenzpoll")

    support.assert_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) is None


def test_asks_for_a_location(app):
    support.send_command(app, "/konkurrenzpoll")

    support.assert_no_dev_error(app)
    assert support.state_of(app) == "LeistungsState:konkurrenzLocation"
    support.assert_said(app, "Schick de nexte location")


def test_location_leads_to_the_date_suggestion(app):
    support.send_command(app, "/konkurrenzpoll")
    support.send_command(app, "Bar A")

    support.assert_no_dev_error(app)
    assert app.poller.type == LeistungsTyp.KONKURENZ
    support.assert_said(app, "Für wann wollen ma pollen?")


def test_poll_question_says_konkurrenz(app):
    support.send_command(app, "/konkurrenzpoll")
    support.send_command(app, "Bar A")
    date_str = support.callback_payloads(support.last_markup(app))[0][
        "🍻poll_date"
    ]

    support.press(app, {"🍻poll_date": date_str})

    support.assert_no_dev_error(app)
    question = app.bot.send_poll.call_args.args[1]
    assert question == f'Konkurrenz Leistungstag 42: am {date_str} in "Bar A"'


def test_publishing_stores_a_konkurrenz_leistungstag(app, db):
    support.send_command(app, "/konkurrenzpoll")
    support.send_command(app, "Bar A")
    date_str = support.callback_payloads(support.last_markup(app))[0][
        "🍻poll_date"
    ]
    support.press(app, {"🍻poll_date": date_str})
    token = support.callback_payloads(support.last_markup(app))[-1][
        "🍻publish"
    ]

    support.press(app, {"🍻publish": token})

    support.assert_no_dev_error(app)
    assert db.addLeistungsTag.call_args.args[4] == int(LeistungsTyp.KONKURENZ)


def test_non_tuesday_is_blasphemy(app, monkeypatch):
    monkeypatch.setattr("leistungsbot.Bot.time.sleep", lambda _: None)
    support.send_command(app, "/konkurrenzpoll")
    support.send_command(app, "Bar A")
    support.press(app, {"🍻poll_date": None})  # "Anderes Datum"

    support.pick_calendar_date(app, next_weekday(4))  # a friday

    support.assert_no_dev_error(app)
    support.assert_said(app, "Blasphemie")
    # warned, but the poll is still sent
    app.bot.send_poll.assert_called_once()
