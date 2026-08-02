# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/switcheroo - move an existing leistungstag to a different location.

/switcheroo -> leistungstag number -> new location -> db
"""

from __future__ import annotations

from tests import support
from tests.fixtures import LOCATION_A
from tests.fixtures import LOCATION_B


def pick_leistungstag(app, number: str = "7") -> None:
    support.send_command(app, "/switcheroo")
    support.send_command(app, number)


def test_asks_for_the_number(app):
    support.send_command(app, "/switcheroo")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Wechan muastn ändern?")
    assert (
        support.state_of(app) == "LeistungsState:switcherooLeistungstagNumber"
    )


def test_pleb_is_rejected(pleb):
    support.send_command(pleb, "/switcheroo")

    support.assert_said(pleb, "nicht für den Pöbel")
    support.assert_not_said(pleb, "Wechan muastn ändern?")
    assert support.state_of(pleb) is None


def test_number_is_looked_up_and_the_new_location_asked_for(app, db):
    pick_leistungstag(app, "7")

    support.assert_no_dev_error(app)
    db.getLeistungstagByNumber.assert_called_once_with(7)
    support.assert_said(app, "Wo schau ma stottdessen hin?")
    assert support.button_labels(support.last_markup(app)) == [
        "Bar A",
        "Bar B",
    ]
    assert (
        support.state_of(app) == "LeistungsState:switcherooAlternateLocation"
    )


def test_unknown_number_stops_the_workflow(app, db):
    db.getLeistungstagByNumber.side_effect = lambda number: None

    pick_leistungstag(app, "999")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Den Leistungstog find i ned")
    support.assert_not_said(app, "Wo schau ma stottdessen hin?")


def test_a_word_is_not_a_number(app, db):
    pick_leistungstag(app, "sieben")

    support.assert_no_dev_error(app)
    support.assert_said(app, "Host du in da Voikschui ned aufpasst")
    db.getLeistungstagByNumber.assert_not_called()
    assert (
        support.state_of(app) == "LeistungsState:switcherooLeistungstagNumber"
    )


def test_switching_updates_the_database(app, db):
    pick_leistungstag(app, "7")

    support.send_command(app, "Bar B")

    support.assert_no_dev_error(app)
    db.switchLeistungstagLocation.assert_called_once_with(
        107,  # key of leistungstag number 7
        LOCATION_A["key"],  # old location
        LOCATION_B["key"],  # new location
    )
    support.assert_said(app, "Ok, donn gemma am 04.08.2026 ins Bar B")
    assert support.state_of(app) is None


def test_unknown_new_location_is_offered_for_adding(app, db):
    pick_leistungstag(app, "7")
    db.getLocationInfo.side_effect = lambda name: None

    support.send_command(app, "Kneipe zum Nix")

    support.assert_no_dev_error(app)
    support.assert_said(app, "kenn i ned")
    assert {"🍻q": "Kneipe zum Nix"} in support.callback_payloads(
        support.last_markup(app),
    )
    assert support.state_of(app) == "LeistungsState:searchLocation"
    db.switchLeistungstagLocation.assert_not_called()


def test_lost_context_aborts_instead_of_switching(app, db):
    support.send_command(app, "/switcheroo")
    support.send_command(app, "7")
    app.user_context.clear()  # e.g. the bot was restarted in between

    support.send_command(app, "Bar B")

    support.assert_said(app, "Could not find Leistungstag in UserContext")
    db.switchLeistungstagLocation.assert_not_called()
    assert support.state_of(app) is None
