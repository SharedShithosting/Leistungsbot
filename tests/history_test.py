# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/history - browse past leistungstage.

/history -> 🍻history_type (typ) -> 🍻history (leistungstag) -> info card
"""

from __future__ import annotations

import pytest

from leistungsbot.BotHelper import LeistungsTyp
from tests import support
from tests.fixtures import LOCATION_A
from tests.fixtures import make_leistungstag


def test_everyone_may_look_at_the_history(pleb):
    support.send_command(pleb, "/history")

    support.assert_no_dev_error(pleb)
    support.assert_not_said(pleb, "nicht für den Pöbel")
    support.assert_said(
        pleb,
        "Welche Art von Leistungstag willst da anschaun?",
    )


def test_offers_every_leistungstag_type(app):
    support.send_command(app, "/history")

    support.assert_no_dev_error(app)
    assert support.callback_payloads(support.last_markup(app)) == [
        {"🍻history_type": int(typ)} for typ in LeistungsTyp
    ]
    assert support.button_labels(support.last_markup(app)) == [
        "NORMAL",
        "KONKURENZ",
        "ZUSATZ",
    ]


@pytest.mark.parametrize("typ", list(LeistungsTyp))
def test_type_selection_lists_that_history(app, db, typ):
    support.send_command(app, "/history")

    support.press(app, {"🍻history_type": int(typ)})

    support.assert_no_dev_error(app)
    db.getHistory.assert_called_once_with(typ, 100)
    support.assert_said(app, "Welchen Leistungstag willst da anschaun?")


def test_history_entries_are_numbered(app, db):
    db.getHistory.return_value = [
        make_leistungstag(key=10, location=1),
        make_leistungstag(key=11, location=2),
    ]
    support.send_command(app, "/history")

    support.press(app, {"🍻history_type": int(LeistungsTyp.NORMAL)})

    support.assert_no_dev_error(app)
    assert support.button_labels(support.last_markup(app)) == [
        "1.Bar A",
        "2.Bar B",
    ]
    assert support.callback_payloads(support.last_markup(app)) == [
        {"🍻history": 10},
        {"🍻history": 11},
    ]


def test_selecting_an_entry_shows_the_info_card(app, db):
    support.send_command(app, "/history")
    support.press(app, {"🍻history_type": int(LeistungsTyp.NORMAL)})

    support.press(app, {"🍻history": 10})

    support.assert_no_dev_error(app)
    db.getLeistungstag.assert_called_with(10)
    db.getAvgLocationRating.assert_called_with(LOCATION_A["name"])

    card = support.sent_texts(app)[-1]
    assert card.startswith("*Bar A*")
    assert "04" in card and "08" in card and "2026" in card  # escaped date
    assert "🌕🌕🌕🌕🌑" in card  # rating 4.0 out of 5
    assert LOCATION_A["address"] in card
    assert LOCATION_A["phone"] in card
    assert app.bot.send_message.call_args.kwargs["parse_mode"] == "MarkdownV2"


def test_ratings_are_rendered_as_moons(app, db):
    db.getAvgLocationRating.return_value = 3.5
    support.send_command(app, "/history")
    support.press(app, {"🍻history_type": int(LeistungsTyp.NORMAL)})

    support.press(app, {"🍻history": 10})

    support.assert_no_dev_error(app)
    assert "🌕🌕🌕🌗🌑" in support.sent_texts(app)[-1]


def test_empty_history_offers_nothing(app, db):
    db.getHistory.return_value = []
    support.send_command(app, "/history")

    support.press(app, {"🍻history_type": int(LeistungsTyp.NORMAL)})

    support.assert_no_dev_error(app)
    assert support.button_labels(support.last_markup(app)) == []
