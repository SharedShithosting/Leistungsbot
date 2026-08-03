# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The calendar, from the database side.

Two halves. The lower one is `LeistungsDB` announcing its writes, tested
against a real database file, and the upper one is `CalendarSync` turning
those announcements into calendar entries, tested against a calendar that
only remembers what it was told.

No google anywhere in here - that is `google_calendar_test.py`. What a
second backend would have to satisfy is `FakeCalendar` below.
"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from leistungsbot import leistungs_calendar
from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.leistungs_calendar import Calendar
from leistungsbot.leistungs_calendar import CalendarSync
from leistungsbot.leistungs_calendar import event_uid
from leistungsbot.leistungs_db import Change
from leistungsbot.leistungs_db import LeistungsDB

PLACE_A = {
    "geometry": {"location": {"lat": 48.3, "lng": 14.28}},
    "formatted_address": "Adresse A",
    "international_phone_number": "+43 1",
    "url": "https://maps.example/a",
}

WHEN = date(2026, 8, 4)


class FakeCalendar(Calendar):
    """Every `Calendar` call, in order, and what the calendar ends up with."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.events: dict = {}

    def add_event(self, event) -> None:
        self.calls.append(("add", event.uid))
        self.events[event.uid] = event

    def update_event(self, event) -> None:
        self.calls.append(("update", event.uid))
        self.events[event.uid] = event

    def remove_event(self, uid: str) -> None:
        self.calls.append(("remove", uid))
        self.events.pop(uid, None)

    def existing_events(self) -> dict:
        self.calls.append(("list", ""))
        return dict(self.events)

    @property
    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.calls]


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
    db.addLocation("place-a", "Bar A")
    db.addLocation("place-b", "Bar B")
    return db


@pytest.fixture
def calendar() -> FakeCalendar:
    return FakeCalendar()


@pytest.fixture(autouse=True)
def _no_pacing(monkeypatch):
    """The startup pass waits between two entries; not in here it does not.

    `test_the_backfill_paces_itself` is what says the pause is real.
    """
    monkeypatch.setattr(leistungs_calendar, "BACKFILL_PAUSE", 0)


@pytest.fixture
def sync(db, calendar) -> CalendarSync:
    """The sync, wired to the database the way `Helper` wires it."""
    sync = CalendarSync(calendar, db, "Europe/Vienna")
    db.subscribe(sync.on_change)
    return sync


def add_leistungstag(
    db,
    name: str = "Bar A",
    when: date = WHEN,
    type: LeistungsTyp = LeistungsTyp.NORMAL,
    poll_id: int = 555,
) -> int:
    return db.addLeistungsTag(when, name, poll_id, poll_id - 1, int(type))


def forget(calendar) -> None:
    """The calendar has never heard of any of it.

    Which is the situation the startup pass is for: leistungstage that
    were in the database before there was a calendar. The `sync` fixture
    is subscribed, so anything added through it has already been
    announced - this undoes that.
    """
    calendar.events.clear()
    calendar.calls.clear()


# ──────────────────────── the database announces ────────────────────────


def test_a_new_leistungstag_is_announced(db):
    seen = []
    db.subscribe(lambda change, lt: seen.append((change, lt["key"])))

    key = add_leistungstag(db)

    assert seen == [(Change.CREATED, key)]


def test_adding_returns_the_new_key(db):
    key = add_leistungstag(db, poll_id=777)

    assert key == db.getLeistungsTagKeyPollId(777)


def test_closing_is_an_update(db):
    key = add_leistungstag(db)
    seen = []
    db.subscribe(lambda change, lt: seen.append((change, lt["closed"])))

    db.closeLeistungstag(key)

    assert seen == [(Change.UPDATED, 1)]


def test_moving_it_is_an_update(db):
    key = add_leistungstag(db)
    seen = []
    db.subscribe(lambda change, lt: seen.append((change, lt["location"])))

    db.switchLeistungstagLocation(
        key,
        db.getLocationKey("Bar A"),
        db.getLocationKey("Bar B"),
    )

    assert seen == [(Change.UPDATED, db.getLocationKey("Bar B"))]


def test_removing_it_is_announced_with_the_row_it_deleted(db):
    key = add_leistungstag(db)
    seen = []
    db.subscribe(lambda change, lt: seen.append((change, lt["key"])))

    db.removeLeistungstag(key)

    assert seen == [(Change.REMOVED, key)]
    assert db.getLeistungstag(key) is None


def test_removing_something_that_is_not_there_says_nothing(db):
    seen = []
    db.subscribe(lambda change, lt: seen.append(change))

    db.removeLeistungstag(4711)

    assert seen == []


def test_a_listener_that_raises_does_not_break_the_write(db):
    db.subscribe(MagicMock(side_effect=RuntimeError("calendar is down")))

    key = add_leistungstag(db)

    assert db.getLeistungstag(key)["poll_id"] == 555


def test_a_listener_that_raises_does_not_stop_the_next_one(db):
    second = MagicMock()
    db.subscribe(MagicMock(side_effect=RuntimeError("calendar is down")))
    db.subscribe(second)

    add_leistungstag(db)

    second.assert_called_once()


def test_nobody_listening_is_fine(db):
    assert add_leistungstag(db)


# ─────────────────────────── the sync reacts ────────────────────────────


def test_a_new_leistungstag_reaches_the_calendar(db, calendar, sync):
    key = add_leistungstag(db)

    assert calendar.calls == [("add", event_uid(key))]


def test_closing_updates_the_entry(db, calendar, sync):
    key = add_leistungstag(db)

    db.closeLeistungstag(key)

    assert calendar.kinds == ["add", "update"]


def test_moving_it_updates_the_entry(db, calendar, sync):
    key = add_leistungstag(db)

    db.switchLeistungstagLocation(
        key,
        db.getLocationKey("Bar A"),
        db.getLocationKey("Bar B"),
    )

    assert calendar.kinds == ["add", "update"]
    assert "Bar B" in calendar.events[event_uid(key)].summary


def test_purging_takes_the_entry_out_again(db, calendar, sync):
    key = add_leistungstag(db)

    db.removeLeistungstag(key)

    assert calendar.kinds == ["add", "remove"]
    assert calendar.events == {}


def test_two_leistungstage_get_two_entries(db, calendar, sync):
    first = add_leistungstag(db, poll_id=1)
    second = add_leistungstag(db, name="Bar B", poll_id=2)

    assert set(calendar.events) == {event_uid(first), event_uid(second)}


def test_a_calendar_that_is_down_does_not_break_the_write(db, sync):
    sync.calendar = MagicMock(spec=Calendar)
    sync.calendar.add_event.side_effect = RuntimeError("no calendar")

    key = add_leistungstag(db)

    assert db.getLeistungstag(key)["poll_id"] == 555


# ──────────────────────────── the startup pass ──────────────────────────


def test_the_backfill_puts_everything_into_the_calendar(db, calendar, sync):
    """The leistungstage that predate the calendar: nothing announced them,
    so only this ever gets them there."""
    keys = [
        add_leistungstag(db, when=date(2026, 8, 4), poll_id=1),
        add_leistungstag(db, when=date(2026, 8, 11), poll_id=2),
    ]
    forget(calendar)

    assert sync.backfill() == 2
    assert set(calendar.events) == {event_uid(key) for key in keys}


def test_the_backfill_updates_rather_than_adds(db, calendar, sync):
    """After the first start every entry is already there. Asking for it to
    be created spends a request on being told so, and a burst of those is
    what google answers with "Rate Limit Exceeded"."""
    add_leistungstag(db)
    forget(calendar)

    sync.backfill()

    assert calendar.kinds == ["list", "update"]


def test_the_backfill_starts_with_the_oldest(db, calendar, sync):
    old = add_leistungstag(db, when=date(2026, 8, 4), poll_id=1)
    new = add_leistungstag(db, when=date(2026, 8, 11), poll_id=2)
    forget(calendar)

    sync.backfill()

    assert calendar.calls == [
        ("list", ""),
        ("update", event_uid(old)),
        ("update", event_uid(new)),
    ]


def test_the_backfill_paces_itself(db, calendar, sync, monkeypatch):
    """Fifty writes to one calendar in a row is what google refuses."""
    monkeypatch.setattr(leistungs_calendar, "BACKFILL_PAUSE", 0.5)
    slept = []
    monkeypatch.setattr(
        leistungs_calendar,
        "sleep",
        lambda seconds: slept.append(seconds),
    )
    for poll_id in (1, 2, 3):
        add_leistungstag(db, poll_id=poll_id)
    forget(calendar)

    sync.backfill()

    assert slept == [0.5, 0.5], "waits between writes, not before the first"


def test_the_backfill_gives_up_after_enough_refusals(db, calendar, sync):
    """A calendar that says no five times running is rate limited, and
    asking another forty times is what got it there."""
    for poll_id in range(1, 9):
        add_leistungstag(db, poll_id=poll_id)
    refusing = MagicMock(spec=Calendar)
    refusing.update_event.side_effect = RuntimeError("Rate Limit Exceeded")
    sync.calendar = refusing

    assert sync.backfill() == 0
    assert refusing.update_event.call_count == (
        leistungs_calendar.BACKFILL_GIVE_UP
    )


def test_a_success_in_between_resets_the_patience(db, calendar, sync):
    """Only failures *in a row* mean the calendar is having none of it."""
    for poll_id in range(1, 8):
        add_leistungstag(db, poll_id=poll_id)
    flaky = MagicMock(spec=Calendar)
    flaky.update_event.side_effect = [
        RuntimeError("no"),
        RuntimeError("no"),
        RuntimeError("no"),
        RuntimeError("no"),
        None,
        RuntimeError("no"),
        None,
    ]
    sync.calendar = flaky

    assert sync.backfill() == 2
    assert flaky.update_event.call_count == 7


def test_the_backfill_of_an_empty_database_does_nothing(db, calendar, sync):
    """Not even the one request it takes to ask what is there."""
    assert sync.backfill() == 0
    assert calendar.calls == []


def test_repeating_the_backfill_does_not_duplicate_anything(
    db,
    calendar,
    sync,
):
    """It runs at every start, so it has to be safe to repeat."""
    add_leistungstag(db)

    sync.backfill()
    sync.backfill()

    assert len(calendar.events) == 1


def test_the_backfill_asks_what_is_there_before_writing(db, calendar, sync):
    add_leistungstag(db)
    calendar.calls.clear()

    sync.backfill()

    assert calendar.calls[0] == ("list", "")


def test_entries_that_are_already_right_are_left_alone(db, calendar, sync):
    """The usual start: nothing to do, and one request to find that out."""
    for poll_id in (1, 2, 3):
        add_leistungstag(db, poll_id=poll_id)
    sync.backfill()
    calendar.calls.clear()

    assert sync.backfill() == 0
    assert calendar.kinds == ["list"]


def test_an_entry_that_says_something_else_is_written(db, calendar, sync):
    """A write that was refused last time, or somebody editing the entry in
    the calendar."""
    key = add_leistungstag(db)
    sync.backfill()
    calendar.events[event_uid(key)].summary = "Was ganz anderes"
    calendar.calls.clear()

    assert sync.backfill() == 1
    assert calendar.kinds == ["list", "update"]


def test_an_entry_that_is_not_there_is_written(db, calendar, sync):
    key = add_leistungstag(db)
    sync.backfill()
    del calendar.events[event_uid(key)]
    calendar.calls.clear()

    assert sync.backfill() == 1
    assert calendar.kinds == ["list", "update"]


def test_only_the_entries_that_need_it_are_written(db, calendar, sync):
    add_leistungstag(db, poll_id=1)
    stale = add_leistungstag(db, poll_id=2)
    add_leistungstag(db, poll_id=3)
    sync.backfill()
    del calendar.events[event_uid(stale)]
    calendar.calls.clear()

    sync.backfill()

    assert calendar.calls == [("list", ""), ("update", event_uid(stale))]


def test_a_calendar_that_will_not_say_gets_everything(db, calendar, sync):
    """Not knowing is slower, not wrong."""
    add_leistungstag(db, poll_id=1)
    add_leistungstag(db, poll_id=2)
    silent = MagicMock(spec=Calendar)
    silent.existing_events.side_effect = RuntimeError("no reading either")
    sync.calendar = silent

    assert sync.backfill() == 2
    assert silent.update_event.call_count == 2


def test_a_backend_that_cannot_list_gets_everything(db, calendar, sync):
    """`existing_events` is optional - the base class answers with nothing."""
    from leistungsbot.leistungs_calendar import Calendar as Base

    add_leistungstag(db)
    forget(calendar)

    assert Base.existing_events(calendar) == {}
    assert sync.backfill() == 1


def test_one_entry_that_fails_does_not_cost_the_rest(db, calendar, sync):
    add_leistungstag(db, poll_id=1)
    add_leistungstag(db, poll_id=2)
    add_leistungstag(db, poll_id=3)
    failing = MagicMock(spec=Calendar)
    failing.update_event.side_effect = [RuntimeError("gone"), None, None]
    sync.calendar = failing

    assert sync.backfill() == 2
    assert failing.update_event.call_count == 3


# ────────────────────────── what an entry says ──────────────────────────


def test_the_entry_spans_the_evening(db, calendar, sync):
    key = add_leistungstag(db)

    event = calendar.events[event_uid(key)]
    assert event.start == datetime(2026, 8, 4, 19, 0)
    assert event.end == datetime(2026, 8, 4, 22, 0)


def test_the_entry_carries_the_configured_timezone(db, calendar):
    sync = CalendarSync(calendar, db, "Europe/Berlin")
    db.subscribe(sync.on_change)

    key = add_leistungstag(db)

    assert calendar.events[event_uid(key)].timezone == "Europe/Berlin"


def test_the_timezone_falls_back_to_the_containers(db, calendar, monkeypatch):
    """`TZ` is what the app was told its local time is."""
    monkeypatch.setenv("TZ", "Europe/Berlin")

    assert CalendarSync(calendar, db).timezone == "Europe/Berlin"


def test_a_configured_timezone_beats_the_containers(db, calendar, monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Berlin")

    assert CalendarSync(calendar, db, "Europe/Vienna").timezone == (
        "Europe/Vienna"
    )


def test_the_timezone_falls_back_to_vienna(db, calendar, monkeypatch):
    monkeypatch.delenv("TZ", raising=False)

    assert CalendarSync(calendar, db).timezone == "Europe/Vienna"


def test_an_empty_timezone_is_no_timezone(db, calendar, monkeypatch):
    """runtipi hands over the fields that were left blank as well."""
    monkeypatch.delenv("TZ", raising=False)

    assert CalendarSync(calendar, db, "").timezone == "Europe/Vienna"


@pytest.mark.parametrize(
    ("type", "expected"),
    [
        (LeistungsTyp.NORMAL, "Leistungstag: Bar A"),
        (LeistungsTyp.KONKURENZ, "Konkurrenz Leistungstag: Bar A"),
        (LeistungsTyp.ZUSATZ, "Leistungstag Zusatztermin: Bar A"),
    ],
)
def test_the_title_says_which_kind_it_is(db, calendar, sync, type, expected):
    key = add_leistungstag(db, type=type)

    assert calendar.events[event_uid(key)].summary == expected


def test_an_unknown_type_still_gets_a_title(db, calendar, sync):
    event = sync.event_for(
        {
            "key": 1,
            "location": db.getLocationKey("Bar A"),
            "date": WHEN,
            "type": 99,
            "closed": 0,
        },
    )

    assert event.summary == "Leistungstag: Bar A"


def test_the_entry_carries_the_address(db, calendar, sync):
    key = add_leistungstag(db)

    assert calendar.events[event_uid(key)].location == "Adresse A"


def test_an_open_poll_is_mentioned(db, calendar, sync):
    key = add_leistungstag(db)

    assert "Abstimmung" in calendar.events[event_uid(key)].description


def test_a_closed_poll_is_not(db, calendar, sync):
    key = add_leistungstag(db)

    db.closeLeistungstag(key)

    assert "Abstimmung" not in calendar.events[event_uid(key)].description


def test_the_description_tells_you_how_to_get_there(db, calendar, sync):
    key = add_leistungstag(db)

    description = calendar.events[event_uid(key)].description
    assert "+43 1" in description
    assert "https://maps.example/a" in description


def test_a_location_that_is_gone_does_not_break_the_entry(db, calendar, sync):
    event = sync.event_for(
        {"key": 7, "location": 4711, "date": WHEN, "type": 1, "closed": 1},
    )

    assert event.summary == "Leistungstag"
    assert event.location == ""


def test_the_uid_is_derived_from_the_key():
    assert event_uid(42) == "leistungstag42"


def test_the_uid_is_an_id_google_accepts():
    """Base32hex: the digits and `a` to `v`, at least five characters."""
    uid = event_uid(1)

    assert len(uid) >= 5
    assert all(
        character in "0123456789abcdefghijklmnopqrstuv" for character in uid
    )


# ───────────────────────────── configuration ────────────────────────────


def test_without_a_calendar_section_there_is_no_sync(db):
    assert leistungs_calendar.from_config(db) is None


def test_a_section_without_a_calendar_id_is_refused(db, monkeypatch):
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {"provider": "google", "calendar_id": None},
    )

    assert leistungs_calendar.from_config(db) is None


def test_a_section_of_empty_fields_is_not_complained_about(db, monkeypatch):
    """runtipi passes every field it knows, blank ones included - that is a
    deployment saying it does not want a calendar, not a broken one."""
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {"provider": "google", "calendar_id": "", "credentials": ""},
    )
    warned = MagicMock()
    monkeypatch.setattr("logging.warning", warned)

    assert leistungs_calendar.from_config(db) is None
    warned.assert_not_called()


def test_a_key_without_a_calendar_id_is_complained_about(db, monkeypatch):
    """Half a section is somebody who meant to configure one."""
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {"calendar_id": "", "credentials": "/config/key.json"},
    )
    warned = MagicMock()
    monkeypatch.setattr("logging.warning", warned)

    assert leistungs_calendar.from_config(db) is None
    warned.assert_called_once()


def test_an_unknown_provider_is_refused(db, monkeypatch):
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {"provider": "outlook", "calendar_id": "whatever"},
    )

    assert leistungs_calendar.from_config(db) is None


def test_google_is_built_from_the_configuration(db, monkeypatch):
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {
            "calendar_id": "cal-1",
            "credentials": "/nowhere/key.json",
            "timezone": "Europe/Berlin",
        },
    )
    built = MagicMock()
    monkeypatch.setattr(
        "leistungsbot.google_calendar.GoogleCalendar",
        built,
    )

    sync = leistungs_calendar.from_config(db)

    built.assert_called_once_with("cal-1", "/nowhere/key.json")
    assert sync.timezone == "Europe/Berlin"


def test_a_backend_that_cannot_be_reached_is_not_a_crash(db, monkeypatch):
    """A missing key file must not stop the bot from starting."""
    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "calendar",
        {"calendar_id": "cal-1", "credentials": "/nowhere/key.json"},
    )
    monkeypatch.setattr(
        "leistungsbot.google_calendar.GoogleCalendar",
        MagicMock(side_effect=OSError("no such file")),
    )

    assert leistungs_calendar.from_config(db) is None
