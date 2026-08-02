# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/leistungspoll - the main workflow.

/leistungspoll -> location -> date -> open hours -> dry run -> publish
"""

from __future__ import annotations

from datetime import datetime

import pytest

from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.google_place import Openness
from tests import support
from tests.fixtures import LOCATION_A
from tests.fixtures import POLL_MESSAGE_ID
from tests.fixtures import VENUE_MESSAGE_ID

DATEFORMAT = "%d.%m.%Y"


def start_poll(app, location: str = "Bar A") -> str:
    """Run /leistungspoll up to the point where a date is asked for.

    Returns the date string offered by the date suggester.
    """
    support.send_command(app, "/leistungspoll")
    support.send_command(app, location)
    support.assert_no_dev_error(app)
    payloads = support.callback_payloads(support.last_markup(app))
    return payloads[0]["🍻poll_date"]


def dry_run(app, location: str = "Bar A") -> int:
    """Run /leistungspoll up to the dry run and return the publish token."""
    date_str = start_poll(app, location)
    support.press(app, {"🍻poll_date": date_str})
    support.assert_no_dev_error(app)
    return support.callback_payloads(support.last_markup(app))[-1]["🍻publish"]


def test_pleb_is_rejected(pleb):
    support.send_command(pleb, "/leistungspoll")

    support.assert_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) is None


def test_asks_for_a_location(app):
    support.send_command(app, "/leistungspoll")

    support.assert_no_dev_error(app)
    assert support.state_of(app) == "LeistungsState:normalLocation"
    support.assert_said(app, "Schick de nexte location")
    assert support.button_labels(support.last_markup(app)) == [
        "Bar A",
        "Bar B",
    ]


def test_known_location_leads_to_the_date_question(app):
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Bar A")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Für wann wollen ma pollen?")
    assert support.poller_of(app).location == "Bar A"
    assert support.poller_of(app).type == LeistungsTyp.NORMAL
    # the location question is answered, the state has to be gone again
    assert support.state_of(app) is None


def test_suggested_date_is_the_next_tuesday(app):
    date_str = start_poll(app)

    assert datetime.strptime(date_str, DATEFORMAT).weekday() == 1


def test_unknown_location_is_offered_for_adding(app, db):
    db.getLocationInfo.side_effect = lambda name: None

    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Kneipe zum Nix")

    support.assert_no_dev_error(app)
    support.assert_said(app, "kenn i ned")
    assert {"🍻q": "Kneipe zum Nix"} in support.callback_payloads(
        support.last_markup(app),
    )
    assert support.state_of(app) == "LeistungsState:searchLocation"


def test_visited_location_warns_but_continues(app, db):
    db.getLocationInfo.side_effect = lambda name: {
        **LOCATION_A,
        "visited": True,
    }

    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Bar A")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Do woan ma schomoi")
    support.assert_said(app, "Für wann wollen ma pollen?")
    assert support.poller_of(app).location == "Bar A"


def test_open_location_goes_straight_to_the_dry_run(app, db, google):
    date_str = start_poll(app)

    support.press(app, {"🍻poll_date": date_str})

    support.assert_no_dev_error(app)
    google.checkOpenHours.assert_called_once()
    assert (
        google.checkOpenHours.call_args.args[0]
        == LOCATION_A["google-place-id"]
    )

    venue = app.bot.send_venue.call_args
    assert venue.kwargs["title"] == LOCATION_A["name"]
    assert venue.kwargs["latitude"] == LOCATION_A["lat"]

    poll = app.bot.send_poll.call_args
    # getHistoryCount is 41, so this is number 42
    assert poll.args[1] == f'Leistungstag 42: am {date_str} in "Bar A"'
    assert poll.args[2] == ["Bin dabei", "Keine Zeit"]

    support.assert_said(app, "Woin ma des so veröffentlichen?")
    # nothing is written to the db before publishing
    db.addLeistungsTag.assert_not_called()


@pytest.mark.parametrize(
    "openness,question",
    [
        (Openness.CLOSED, "I glaub ned, dass de offn hom"),
        (Openness.SHORT, "Is da des long gmua?"),
        (Openness.UNKNOWN, "I was jetzt hod ned, ob de offen hom"),
    ],
)
def test_doubtful_open_hours_ask_back(app, google, openness, question):
    google.checkOpenHours.return_value = (openness, "Dienstag: geschlossen")
    date_str = start_poll(app)

    support.press(app, {"🍻poll_date": date_str})

    support.assert_no_dev_error(app)
    support.assert_said(app, question)
    app.bot.send_poll.assert_not_called()
    assert {"🍻open_hours_checked": True} in support.callback_payloads(
        support.last_markup(app),
    )


def test_confirming_the_open_hours_sends_the_dry_run(app, google):
    google.checkOpenHours.return_value = (
        Openness.CLOSED,
        "Dienstag: geschlossen",
    )
    date_str = start_poll(app)
    support.press(app, {"🍻poll_date": date_str})

    support.press(app, {"🍻open_hours_checked": True})

    support.assert_no_dev_error(app)
    app.bot.send_poll.assert_called_once()
    assert support.poller_of(app).date.strftime(DATEFORMAT) == date_str


def test_aborting_the_open_hours_sends_nothing(app, google):
    google.checkOpenHours.return_value = (
        Openness.CLOSED,
        "Dienstag: geschlossen",
    )
    date_str = start_poll(app)
    support.press(app, {"🍻poll_date": date_str})

    support.press(app, {"🍻open_hours_checked": False})

    support.assert_no_dev_error(app)
    app.bot.send_poll.assert_not_called()


def test_publishing_stores_the_leistungstag(app, db):
    token = dry_run(app)

    support.press(app, {"🍻publish": token})

    support.assert_no_dev_error(app)
    db.addLeistungsTag.assert_called_once()
    date, location, poll_id, venue_id, type_ = (
        db.addLeistungsTag.call_args.args
    )
    assert location == "Bar A"
    assert poll_id == POLL_MESSAGE_ID
    assert venue_id == VENUE_MESSAGE_ID
    assert type_ == int(LeistungsTyp.NORMAL)
    assert date.weekday() == 1

    db.setLocationVisitedState.assert_called_once_with("Bar A", True)
    app.bot.pin_chat_message.assert_called_once_with(
        support.LEISTUNGSCHAT_ID,
        POLL_MESSAGE_ID,
    )
    support.assert_said(app, "Hauma so veröffentlicht")


def test_publishing_goes_to_the_leistungschat(app):
    token = dry_run(app)

    support.press(app, {"🍻publish": token})

    support.assert_no_dev_error(app)
    assert app.bot.send_poll.call_args.args[0] == support.LEISTUNGSCHAT_ID
    assert app.bot.send_venue.call_args.args[0] == support.LEISTUNGSCHAT_ID


def test_cancel_clears_the_state(app):
    support.send_command(app, "/leistungspoll")

    support.send_command(app, "/cancel")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Halt Stop.")
    assert support.state_of(app) is None
