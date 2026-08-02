# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/add_location - google search, pick a candidate, confirm, store.

/add_location -> query -> 🍻search (pick) -> 🍻select (confirm) -> db
"""

from __future__ import annotations

from leistungsbot.leistungs_returns import LeistungsReturnCodes
from tests import support
from tests.fixtures import GOOGLE_CANDIDATES
from tests.fixtures import GOOGLE_PLACE_INFO


def search(app, query: str = "Bar") -> list[dict]:
    """Run /add_location up to the candidate list; returns its payloads."""
    support.send_command(app, "/add_location")
    support.send_command(app, query)
    support.assert_no_dev_error(app)
    return support.callback_payloads(support.last_markup(app))


def test_everyone_may_add_a_location(pleb):
    support.send_command(pleb, "/add_location")

    support.assert_no_dev_error(pleb)
    support.assert_not_said(pleb, "nicht für den Pöbel")
    assert support.state_of(pleb) == "LeistungsState:searchLocation"
    support.assert_said(pleb, "Schick dei location idee")


def test_query_is_passed_to_google(app, google):
    search(app, "Kaffee Glockenspiel")

    google.findPlace.assert_called_once_with("Kaffee Glockenspiel")


def test_several_hits_are_offered_for_choosing(app):
    payloads = search(app)

    support.assert_said(app, "Suach da aus wost willst")
    assert [p["🍻search"][1] for p in payloads] == [0, 1]
    labels = support.button_labels(support.last_markup(app))
    assert "Bar A" in labels[0] and "Adresse A" in labels[0]


def test_no_hit_says_so(app, google):
    google.findPlace.return_value = []

    support.send_command(app, "/add_location")
    support.send_command(app, "Gibtsnicht")

    support.assert_no_dev_error(app)
    support.assert_said(app, 'Wenn i nach "Gibtsnicht" suach find i nix')


def test_single_hit_skips_the_choice(app, google):
    google.findPlace.return_value = [GOOGLE_CANDIDATES[0]]

    support.send_command(app, "/add_location")
    support.send_command(app, "Bar A")

    support.assert_no_dev_error(app)
    support.assert_not_said(app, "Suach da aus wost willst")
    app.bot.send_venue.assert_called_once()
    assert {"🍻select"} <= {
        key
        for p in support.callback_payloads(support.last_markup(app))
        for key in p
    }


def test_picking_a_candidate_shows_it_for_approval(app, google):
    payloads = search(app)

    support.press(app, payloads[1])  # 🍻search -> "Bar B"

    support.assert_no_dev_error(app)
    google.getPlaceInfo.assert_called_with("place-b")
    venue = app.bot.send_venue.call_args
    assert venue.args[3] == GOOGLE_PLACE_INFO["name"]
    assert {
        "🍻select": [payloads[1]["🍻search"][0], 1],
    } in support.callback_payloads(
        support.last_markup(app),
    )


def test_approving_writes_the_location(app, db, google):
    payloads = search(app)
    support.press(app, payloads[0])
    select = support.callback_payloads(support.last_markup(app))[-1]

    support.press(app, select)

    support.assert_no_dev_error(app)
    db.addLocation.assert_called_once_with("place-a", "Bar A")


def test_duplicate_location_is_reported(app, db):
    db.addLocation.return_value = LeistungsReturnCodes.DB_DUPLICATE
    payloads = search(app)
    support.press(app, payloads[0])
    select = support.callback_payloads(support.last_markup(app))[-1]

    support.press(app, select)

    support.assert_no_dev_error(app)
    support.assert_said(app, "Des isch scho drin, du deppata!")


def test_rejecting_offers_the_other_candidates_again(app, db):
    payloads = search(app)
    support.press(app, payloads[0])
    rand_id = payloads[0]["🍻search"][0]

    support.press(app, {"🍻select": [rand_id, -1]})

    support.assert_no_dev_error(app)
    support.assert_said(app, "Daun probiern mas numoi")
    assert support.button_labels(support.last_markup(app)) == [
        "Bar A",
        "Bar B",
    ]
    db.addLocation.assert_not_called()


def test_rejecting_the_only_candidate_asks_for_a_better_query(app, google):
    google.findPlace.return_value = [GOOGLE_CANDIDATES[0]]
    support.send_command(app, "/add_location")
    support.send_command(app, "Bar A")
    select = support.callback_payloads(support.last_markup(app))[0]
    rand_id = select["🍻select"][0]

    support.press(app, {"🍻select": [rand_id, -1]})

    support.assert_no_dev_error(app)
    support.assert_said(app, "Daun füg a boa mehr infos zu deiner Suche dazua")


def test_unknown_poll_location_can_be_searched_from_the_poll(app, db):
    """The 🍻q button of /leistungspoll hands over into this workflow."""
    db.getLocationInfo.side_effect = lambda name: None
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Kneipe zum Nix")

    support.press(app, {"🍻q": "Kneipe zum Nix"})

    support.assert_no_dev_error(app)
    support.assert_said(app, "Suach da aus wost willst")
