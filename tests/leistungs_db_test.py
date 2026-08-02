# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""LeistungsDB against a real database.

With SQLite there is no server to reach, so these are ordinary unit tests
that run everywhere - the whole file used to need a MariaDB and was skipped
almost everywhere it ran.
"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.leistungs_db import LeistungsDB
from leistungsbot.leistungs_db import LeistungsTagState
from leistungsbot.leistungs_returns import LeistungsReturnCodes

PLACE_A = {
    "geometry": {"location": {"lat": 48.3, "lng": 14.28}},
    "formatted_address": "Adresse A",
    "international_phone_number": "+43 1",
    "url": "https://maps.example/a",
}


@pytest.fixture
def db(tmp_path, monkeypatch) -> LeistungsDB:
    """A LeistungsDB on a real, empty database file."""
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "sqlite",
        {"path": str(tmp_path / "test.sqlite")},
    )
    monkeypatch.setattr("leistungsbot.leistungs_db.Places", MagicMock())
    db = LeistungsDB()
    db.google.getPlaceInfo.return_value = dict(PLACE_A)
    return db


def add_location(db, name="Bar A", place_id="place-a") -> int:
    db.addLocation(place_id, name)
    return db.getLocationKey(name)


def add_leistungstag(
    db,
    name="Bar A",
    when=date(2026, 8, 4),
    type=LeistungsTyp.NORMAL,
    poll_id=555,
) -> int:
    db.addLeistungsTag(when, name, poll_id, poll_id - 1, int(type))
    return db.getLeistungsTagKeyPollId(poll_id)


# ─────────────────────────────── bootstrapping ──────────────────────────────


def test_a_new_file_gets_the_whole_schema(db):
    tables, views = db.getTables()

    assert tables == [
        "leistungstag",
        "location_rating",
        "locations",
        "members",
        "participants",
    ]
    assert views == [
        "events",
        "konkurrenz_view",
        "leistungs_view",
        "zusatz_view",
    ]


def test_the_database_file_is_created(db, tmp_path):
    assert (tmp_path / "test.sqlite").exists()
    assert db.checkConnection()


def test_reopening_keeps_the_data(db):
    add_location(db)

    db.connect()

    assert db.getLocationKey("Bar A") is not None


def test_foreign_keys_are_enforced(db):
    with pytest.raises(Exception):
        db.cursor().execute(
            'INSERT INTO "leistungstag" '
            '("location", "date", "poll_id", "venue_id", "type") '
            "VALUES (999, '2026-08-04', 1, 2, 1);",
        )


# ───────────────────────────────── locations ────────────────────────────────


def test_a_location_round_trips(db):
    key = add_location(db)

    info = db.getLocationInfo("Bar A")
    assert info["key"] == key
    assert info["name"] == "Bar A"
    assert info["google-place-id"] == "place-a"
    assert info["address"] == "Adresse A"
    assert info["lat"] == 48.3
    assert info["visited"] == 0
    assert db.getLocationInfoByKey(key) == info


def test_an_unknown_location_is_none(db):
    assert db.getLocationInfo("Gibtsnicht") is None
    assert db.getLocationKey("Gibtsnicht") is None


def test_the_same_place_twice_is_a_duplicate(db):
    add_location(db)

    assert (
        db.addLocation("place-a", "Bar A") == LeistungsReturnCodes.DB_DUPLICATE
    )
    assert len(db.getAllLocations()) == 1


def test_the_same_name_for_another_place_gets_a_suffix(db):
    add_location(db)

    assert db.addLocation("place-b", "Bar A") == LeistungsReturnCodes.OK
    assert db.getLocationKey("Bar A2") is not None


def test_visited_splits_the_lists(db):
    add_location(db, "Bar A", "place-a")
    add_location(db, "Bar B", "place-b")

    db.setLocationVisitedState("Bar A", True)

    assert db.getVisitedLocations() == [["Bar A", 1]]
    assert db.getVirgineLocations() == [["Bar B", 2]]


def test_a_location_can_be_removed(db):
    key = add_location(db)

    db.removeLocation(key)

    assert db.getAllLocations() is None


# ────────────────────────────────── members ─────────────────────────────────


def test_a_user_round_trips(db):
    db.addUser(42, 100)

    assert db.getUserKey(42) == 1
    assert db.getUserScore(42) == 0


def test_adding_a_user_twice_updates_instead_of_failing(db):
    db.addUser(42, 100)

    db.addUser(42, 101)

    assert len(db.getUsers()) == 1


def test_a_score_can_be_set(db):
    db.addUser(42)

    db.setUserScore(42, 7)
    db.increaseUserScore(42, 3)

    assert db.getUserScore(42) == 10


# ────────────────────────────────── ratings ─────────────────────────────────


def test_a_rating_averages(db):
    add_location(db)
    db.addUser(42)
    db.addUser(43)

    db.rateLocation("Bar A", 42, 4)
    db.rateLocation("Bar A", 43, 5)

    assert db.getAvgLocationRating("Bar A") == 4.5
    # a dict cursor, same shape the MariaDB version returned
    assert db.getUserLocationRating("Bar A", 42) == {"rating": 4}


def test_rating_twice_is_refused(db):
    add_location(db)
    db.addUser(42)
    db.rateLocation("Bar A", 42, 4)

    with pytest.raises(Exception):
        db.rateLocation("Bar A", 42, 5)


def test_an_unrated_location_is_zero(db):
    add_location(db)

    assert db.getAvgLocationRating("Bar A") == 0


# ──────────────────────────────── leistungstag ──────────────────────────────


def test_a_leistungstag_round_trips(db):
    add_location(db)

    key = add_leistungstag(db)

    lt = db.getLeistungstag(key)
    assert lt["location"] == 1
    assert lt["poll_id"] == 555
    assert lt["type"] == int(LeistungsTyp.NORMAL)
    assert lt["closed"] == 0


def test_the_date_comes_back_as_a_date(db):
    """The callers do strftime and date arithmetic on it."""
    add_location(db)
    key = add_leistungstag(db, when=date(2026, 8, 4))

    stored = db.getLeistungstag(key)["date"]

    assert stored == date(2026, 8, 4)
    assert stored.strftime("%d.%m.%Y") == "04.08.2026"


def test_a_datetime_is_stored_as_the_day(db):
    add_location(db)
    key = add_leistungstag(db, when=datetime(2026, 8, 4, 19, 30))

    assert db.getLeistungstag(key)["date"] == date(2026, 8, 4)


def test_joined_comes_back_as_a_datetime(db):
    db.addUser(42)

    joined = db.getUsers()[0][4]

    assert isinstance(joined, datetime)


def test_closing_moves_it_between_the_lists(db):
    add_location(db)
    key = add_leistungstag(db)
    assert len(db.getOpenLeistungsTag()) == 1

    db.closeLeistungstag(key)

    assert db.getOpenLeistungsTag() is None
    assert len(db.getClosedLeistungsTag()) == 1


def test_by_date_finds_it(db):
    add_location(db)
    add_leistungstag(db, when=date(2026, 8, 4))

    assert len(db.getLeistungstageByDate(date(2026, 8, 4))) == 1
    assert db.getLeistungstageByDate(date(2026, 8, 5)) is None


def test_history_is_ordered_and_limited(db):
    add_location(db, "Bar A", "place-a")
    add_leistungstag(db, when=date(2026, 8, 4), poll_id=1)
    add_leistungstag(db, when=date(2026, 8, 11), poll_id=2)
    add_leistungstag(db, when=date(2026, 8, 18), poll_id=3)

    history = db.getHistory(LeistungsTyp.NORMAL, 2)

    assert [lt["date"] for lt in history] == [
        date(2026, 8, 11),
        date(2026, 8, 18),
    ]
    assert db.getHistoryCount(LeistungsTyp.NORMAL) == 3
    assert db.getHistoryCount() == 3


def test_before_filters_by_date(db):
    add_location(db)
    add_leistungstag(db, when=date(2026, 8, 4), poll_id=1)
    add_leistungstag(db, when=date(2026, 9, 1), poll_id=2)

    past = db.getLeistungsTags(before=datetime(2026, 8, 20, 12, 0))

    assert [lt["date"] for lt in past] == [date(2026, 8, 4)]


def test_the_types_are_kept_apart(db):
    add_location(db)
    add_leistungstag(db, type=LeistungsTyp.NORMAL, poll_id=1)
    add_leistungstag(db, type=LeistungsTyp.KONKURENZ, poll_id=2)
    add_leistungstag(db, type=LeistungsTyp.ZUSATZ, poll_id=3)

    assert len(db.getLeistungsTags(LeistungsTyp.NORMAL)) == 1
    assert len(db.getLeistungsTags(LeistungsTyp.KONKURENZ)) == 1
    assert len(db.getLeistungsTags()) == 3


def test_the_latest_is_the_newest(db):
    add_location(db)
    add_leistungstag(db, when=date(2026, 8, 4), poll_id=1)
    add_leistungstag(db, when=date(2026, 9, 1), poll_id=2)

    assert db.getLatest()["date"] == date(2026, 9, 1)
    assert db.getMostRecentLeistungstag()["date"] == date(2026, 9, 1)


def test_state_filters(db):
    add_location(db)
    open_key = add_leistungstag(db, poll_id=1)
    closed_key = add_leistungstag(db, poll_id=2)
    db.closeLeistungstag(closed_key)

    assert [
        lt["key"] for lt in db.getLeistungsTags(state=LeistungsTagState.OPEN)
    ] == [
        open_key,
    ]


# ──────────────────────────────── views ─────────────────────────────────────


def test_leistungs_view_numbers_by_date(db):
    """This is what /switcheroo looks a Leistungstag up by."""
    add_location(db)
    add_leistungstag(db, when=date(2026, 8, 11), poll_id=2)
    first = add_leistungstag(db, when=date(2026, 8, 4), poll_id=1)

    assert db.getLeistungstagByNumber(1)["key"] == first
    assert db.getLeistungstagByNumber(2)["date"] == date(2026, 8, 11)
    assert db.getLeistungstagByNumber(3) is None


def test_each_type_gets_its_own_numbering(db):
    add_location(db)
    add_leistungstag(db, type=LeistungsTyp.KONKURENZ, poll_id=1)
    normal = add_leistungstag(db, type=LeistungsTyp.NORMAL, poll_id=2)

    assert db.getLeistungstagByNumber(1)["key"] == normal


def test_the_events_view_spans_the_evening(db):
    add_location(db)
    add_leistungstag(db, when=date(2026, 8, 4))

    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM "events";')
    event = db.convert(cursor.fetchone())

    assert event["start"] == datetime(2026, 8, 4, 19, 0)
    assert event["end"] == datetime(2026, 8, 4, 22, 0)


# ───────────────────────────────── switcheroo ───────────────────────────────


def test_switching_moves_the_leistungstag(db):
    a = add_location(db, "Bar A", "place-a")
    b = add_location(db, "Bar B", "place-b")
    key = add_leistungstag(db, "Bar A")
    db.setLocationVisitedState("Bar A", True)

    db.switchLeistungstagLocation(key, a, b)

    assert db.getLeistungstag(key)["location"] == b
    assert db.getLocationInfoByKey(b)["visited"] == 1
    # the old one is free again, nothing else points at it
    assert db.getLocationInfoByKey(a)["visited"] == 0


def test_a_location_still_in_use_stays_visited(db):
    a = add_location(db, "Bar A", "place-a")
    b = add_location(db, "Bar B", "place-b")
    add_leistungstag(db, "Bar A", poll_id=1)
    key = add_leistungstag(db, "Bar A", poll_id=2)

    db.switchLeistungstagLocation(key, a, b)

    assert db.getLocationInfoByKey(a)["visited"] == 1


# ──────────────────────────────── participants ──────────────────────────────


def test_a_participant_round_trips(db):
    add_location(db)
    add_leistungstag(db, poll_id=555)
    db.addUser(42)

    db.addParticipant(42, 555)

    # one row per participant, each a one column row
    assert db.getParticipants(1) == [[1]]
    assert db.getLatestParticipants() == [[1]]
