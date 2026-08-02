# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The list of places a leistungstag can go.

/show_locations, /remove_location and /rate_location. The /add_location
search itself is exercised from the leistungspoll side, this file covers the
commands around it.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tests import support
from tests.fixtures import LOCATION_A
from tests.fixtures import make_leistungstag

STRANGER = "hackl"


# --- /show_locations ----------------------------------------------------


def test_show_locations_lists_the_unvisited_ones(app):
    support.send_command(app, "/show_locations")

    support.assert_said(app, "Des san de nächsten Locations")
    assert support.button_labels(support.last_markup(app)) == [
        LOCATION_A["name"],
        "Bar B",
    ]
    support.assert_no_dev_error(app)


def test_show_locations_survives_a_broken_database(app, db):
    db.getVirgineLocations.side_effect = RuntimeError("no database")

    support.send_command(app, "/show_locations")

    support.assert_said(app, "Hi Devs")  # reported, not swallowed


# --- /add_location ------------------------------------------------------


def test_add_location_asks_for_an_idea(app):
    support.send_command(app, "/add_location")

    support.assert_said(app, "Schick dei location idee muaz")
    assert support.state_of(app) == "LeistungsState:searchLocation"


# --- /remove_location ---------------------------------------------------


def test_remove_location_is_refused_to_a_pleb(pleb):
    support.send_command(pleb, "/remove_location")

    support.assert_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) is None


def test_remove_location_offers_the_list(app):
    support.send_command(app, "/remove_location")

    support.assert_said(app, "Welche Location willst löschen?")
    assert support.state_of(app) == "LeistungsState:removeLocation"


def test_naming_a_location_removes_it(app, db):
    support.send_command(app, "/remove_location")
    support.send_command(app, LOCATION_A["name"])

    db.getLocationKey.assert_called_with(LOCATION_A["name"])
    db.removeLocation.assert_called_once()
    support.assert_said(app, "murz destroyed")


def test_removing_an_unknown_location_is_reported(app, db):
    db.removeLocation.side_effect = RuntimeError("no such location")
    support.send_command(app, "/remove_location")

    support.send_command(app, "Nicht Existent")

    support.assert_said(app, "Hi Devs")


# --- /rate_location -----------------------------------------------------


def test_rating_is_refused_in_a_group(app):
    support.send_command(app, "/rate_location")

    support.assert_said(app, "Gruppenchat")
    assert support.state_of(app) is None


@pytest.fixture
def private(app, db):
    """A private chat with a past leistungstag to rate."""
    db.getLeistungsTags.return_value = [make_leistungstag()]
    app.helper.send_location_info2 = MagicMock(name="send_location_info2")
    return app


def rate_command(app, **kwargs):
    support.send_command(
        app,
        "/rate_location",
        chat_type="private",
        chat_id=support.ADMIN_USER_ID,
        **kwargs,
    )


def test_rating_in_private_asks_for_moons(private):
    rate_command(private)

    support.assert_said(private, "Wiafü Monde")
    support.assert_no_dev_error(private)


def test_rating_in_private_shows_which_location(private):
    rate_command(private)

    private.helper.send_location_info2.assert_called_once()


def test_a_rating_is_stored(private, db):
    rate_command(private)
    support.send_command(
        private,
        private.helper.get_stars(4),
        chat_type="private",
        chat_id=support.ADMIN_USER_ID,
    )

    db.rateLocationKey.assert_called_once()
    assert db.rateLocationKey.call_args.args[2] == pytest.approx(4)


def test_rating_twice_is_called_out(private, db):
    db.rateLocationKey.side_effect = RuntimeError("already voted")
    rate_command(private)

    support.send_command(
        private,
        private.helper.get_stars(4),
        chat_type="private",
        chat_id=support.ADMIN_USER_ID,
    )

    support.assert_said(private, "WAHLBETRUG")


def test_rating_without_a_past_leistungstag_is_reported(app, db):
    db.getLeistungsTags.return_value = []

    rate_command(app)

    support.assert_said(app, "Hi Devs")
