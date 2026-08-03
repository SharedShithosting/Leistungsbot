# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The google calendar wrapper, against a stand in for the api client.

Nothing here reaches google. `GoogleCalendar` takes an already built client,
which is the seam these tests hold on to - the alternative would be a
service account and a real calendar, and then this file would be as skipped
as `google_place_test.py` is.

What is worth testing is not the three api calls, it is the two answers that
are not really errors: inserting an id that is already there, and deleting
one that is not.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from leistungsbot.google_calendar import FIELDS
from leistungsbot.google_calendar import PAGE_SIZE
from leistungsbot.google_calendar import RETRIES
from leistungsbot.google_calendar import GoogleCalendar
from leistungsbot.leistungs_calendar import CalendarEvent

CALENDAR_ID = "leistungs-calendar@group.calendar.google.com"


def http_error(status: int) -> HttpError:
    """What the google client raises, cut down to the part that is read."""
    return HttpError(
        resp=SimpleNamespace(status=status, reason="nope"),
        content=b"{}",
    )


@pytest.fixture
def service() -> MagicMock:
    """A stand in for the discovery client.

    `service.events()` hands back the same child mock every time, so
    `service.events().insert` in a test is the call the code made.
    """
    return MagicMock(name="calendar-v3")


@pytest.fixture
def calendar(service) -> GoogleCalendar:
    return GoogleCalendar(CALENDAR_ID, service=service)


@pytest.fixture
def event() -> CalendarEvent:
    return CalendarEvent(
        uid="leistungstag42",
        summary="Leistungstag: Bar A",
        start=datetime(2026, 8, 4, 19, 0),
        end=datetime(2026, 8, 4, 22, 0),
        location="Adresse A",
        description="+43 1",
        timezone="Europe/Vienna",
    )


# ───────────────────────────── the happy path ───────────────────────────


def test_adding_inserts_the_event(calendar, service, event):
    calendar.add_event(event)

    service.events().insert.assert_called_once()
    kwargs = service.events().insert.call_args.kwargs
    assert kwargs["calendarId"] == CALENDAR_ID
    assert kwargs["body"]["summary"] == "Leistungstag: Bar A"


def test_the_event_carries_our_own_id(calendar, service, event):
    """The id is derived from the leistungstag key, so nothing has to be
    stored to find the event again."""
    calendar.add_event(event)

    assert service.events().insert.call_args.kwargs["body"]["id"] == (
        "leistungstag42"
    )


def test_the_request_is_executed(calendar, service, event):
    calendar.add_event(event)

    service.events().insert().execute.assert_called()


# ─────────────────────────────── backing off ────────────────────────────


def test_a_request_is_allowed_to_be_retried(calendar, service, event):
    """The client turns `num_retries` into a randomised exponential backoff
    over 429, the 5xx family and the rate limited 403s. Its default is
    zero, which is why the startup pass gave up on the first one."""
    calendar.add_event(event)

    assert service.events().insert().execute.call_args.kwargs == {
        "num_retries": RETRIES,
    }


def test_an_update_backs_off_as_well(calendar, service, event):
    calendar.update_event(event)

    assert service.events().update().execute.call_args.kwargs == {
        "num_retries": RETRIES,
    }


def test_a_delete_backs_off_as_well(calendar, service):
    calendar.remove_event("leistungstag42")

    assert service.events().delete().execute.call_args.kwargs == {
        "num_retries": RETRIES,
    }


def test_the_retries_are_worth_having():
    """Zero would mean the setting is there and does nothing."""
    assert RETRIES > 0


def test_updating_writes_over_the_event(calendar, service, event):
    calendar.update_event(event)

    kwargs = service.events().update.call_args.kwargs
    assert kwargs["eventId"] == "leistungstag42"
    assert kwargs["calendarId"] == CALENDAR_ID


def test_an_update_does_not_carry_an_id_in_the_body(calendar, service, event):
    """The id belongs in the path; a body id would be a rename."""
    calendar.update_event(event)

    assert "id" not in service.events().update.call_args.kwargs["body"]


def test_removing_deletes_the_event(calendar, service):
    calendar.remove_event("leistungstag42")

    service.events().delete.assert_called_once_with(
        calendarId=CALENDAR_ID,
        eventId="leistungstag42",
    )


# ──────────────────────────── the body it sends ─────────────────────────


def test_the_times_go_out_with_the_zone_next_to_them(calendar, event):
    """Wall clock time plus a zone, so seven in the evening stays seven
    across a daylight saving change."""
    body = calendar.body(event)

    assert body["start"] == {
        "dateTime": "2026-08-04T19:00:00",
        "timeZone": "Europe/Vienna",
    }
    assert body["end"]["dateTime"] == "2026-08-04T22:00:00"


def test_the_body_says_confirmed(calendar, event):
    """An update on a deleted event revives it - but only if it says so."""
    assert calendar.body(event)["status"] == "confirmed"


def test_the_address_and_the_description_are_carried(calendar, event):
    body = calendar.body(event)

    assert body["location"] == "Adresse A"
    assert body["description"] == "+43 1"


def test_extra_fields_are_passed_through(calendar, event):
    event.extra = {"transparency": "transparent"}

    assert calendar.body(event)["transparency"] == "transparent"


# ──────────────────────────── reading it back ───────────────────────────


def google_event(uid: str = "leistungstag42", **overrides) -> dict:
    """An event resource as the api hands it back."""
    return {
        "id": uid,
        "summary": "Leistungstag: Bar A",
        "location": "Adresse A",
        "description": "+43 1",
        "start": {
            "dateTime": "2026-08-04T19:00:00+02:00",
            "timeZone": "Europe/Vienna",
        },
        "end": {
            "dateTime": "2026-08-04T22:00:00+02:00",
            "timeZone": "Europe/Vienna",
        },
    } | overrides


def test_the_calendar_can_be_read_in_one_request(calendar, service):
    service.events().list().execute.return_value = {
        "items": [
            google_event("leistungstag1"),
            google_event("leistungstag2"),
        ],
    }

    events = calendar.existing_events()

    assert set(events) == {"leistungstag1", "leistungstag2"}
    service.events().list().execute.assert_called_once()


def test_reading_asks_for_a_full_page_and_nothing_it_throws_away(
    calendar,
    service,
):
    service.events().list().execute.return_value = {}

    calendar.existing_events()

    kwargs = service.events().list.call_args.kwargs
    assert kwargs["calendarId"] == CALENDAR_ID
    assert kwargs["maxResults"] == PAGE_SIZE
    assert kwargs["fields"] == FIELDS


def test_an_event_comes_back_the_way_it_went_in(calendar, service, event):
    """What the comparison in the startup pass rests on: an untouched entry
    reads back equal to the one the database describes."""
    service.events().list().execute.return_value = {"items": [google_event()]}

    assert calendar.existing_events()["leistungstag42"] == event


def test_the_offset_is_dropped_rather_than_converted(calendar, service):
    """The api answers in the event's own zone, so the wall clock time is
    what was written - a conversion would make every entry look changed."""
    service.events().list().execute.return_value = {"items": [google_event()]}

    read = calendar.existing_events()["leistungstag42"]

    assert read.start == datetime(2026, 8, 4, 19, 0)
    assert read.start.tzinfo is None
    assert read.timezone == "Europe/Vienna"


def test_every_page_is_read(calendar, service):
    service.events().list().execute.side_effect = [
        {"items": [google_event("leistungstag1")], "nextPageToken": "page-2"},
        {"items": [google_event("leistungstag2")]},
    ]

    events = calendar.existing_events()

    assert set(events) == {"leistungstag1", "leistungstag2"}
    assert service.events().list.call_args.kwargs["pageToken"] == "page-2"


def test_an_all_day_event_is_ignored(calendar, service):
    """Somebody else's entry, in a calendar that is not only ours."""
    service.events().list().execute.return_value = {
        "items": [
            {"id": "urlaub", "start": {"date": "2026-08-04"}, "end": {}},
            google_event(),
        ],
    }

    assert set(calendar.existing_events()) == {"leistungstag42"}


def test_a_missing_description_reads_as_an_empty_one(calendar, service):
    """The api leaves the field out rather than sending an empty string."""
    item = google_event()
    del item["description"]
    service.events().list().execute.return_value = {"items": [item]}

    assert calendar.existing_events()["leistungstag42"].description == ""


def test_an_empty_calendar_reads_as_nothing(calendar, service):
    service.events().list().execute.return_value = {}

    assert calendar.existing_events() == {}


def test_reading_backs_off_as_well(calendar, service):
    service.events().list().execute.return_value = {}

    calendar.existing_events()

    assert service.events().list().execute.call_args.kwargs == {
        "num_retries": RETRIES,
    }


# ────────────────────────── the answers that are not errors ─────────────


def test_adding_something_that_is_there_updates_it(calendar, service, event):
    service.events().insert.side_effect = http_error(409)

    calendar.add_event(event)

    service.events().update.assert_called_once()


def test_updating_something_that_is_gone_adds_it(calendar, service, event):
    service.events().update.side_effect = http_error(404)

    calendar.update_event(event)

    service.events().insert.assert_called_once()


def test_a_deleted_event_is_revived_rather_than_duplicated(
    calendar,
    service,
    event,
):
    """`410 Gone` is what google answers for an event it still remembers
    deleting."""
    service.events().update.side_effect = http_error(410)

    calendar.update_event(event)

    service.events().insert.assert_called_once()


def test_removing_something_that_is_gone_is_fine(calendar, service):
    service.events().delete.side_effect = http_error(404)

    calendar.remove_event("leistungstag42")


def test_the_two_do_not_bounce_off_each_other(calendar, service, event):
    """A conflict on the insert that an update fell back to would loop."""
    service.events().update.side_effect = http_error(404)
    service.events().insert.side_effect = http_error(409)

    with pytest.raises(HttpError):
        calendar.update_event(event)


# ─────────────────────────── the ones that are ──────────────────────────


@pytest.mark.parametrize("status", [401, 403, 500])
def test_a_real_error_on_insert_is_raised(calendar, service, event, status):
    service.events().insert.side_effect = http_error(status)

    with pytest.raises(HttpError):
        calendar.add_event(event)


def test_a_real_error_on_update_is_raised(calendar, service, event):
    service.events().update.side_effect = http_error(403)

    with pytest.raises(HttpError):
        calendar.update_event(event)


def test_a_real_error_on_delete_is_raised(calendar, service):
    service.events().delete.side_effect = http_error(403)

    with pytest.raises(HttpError):
        calendar.remove_event("leistungstag42")


def test_an_error_without_a_response_is_raised(calendar, service, event):
    """Not everything the client raises carries an http status."""
    service.events().insert.side_effect = RuntimeError("socket closed")

    with pytest.raises(RuntimeError):
        calendar.add_event(event)


# ───────────────────────────── authentication ───────────────────────────


def test_a_client_is_built_from_the_service_account(monkeypatch):
    credentials = MagicMock()
    from_file = MagicMock(return_value=credentials)
    build = MagicMock()
    monkeypatch.setattr(
        "leistungsbot.google_calendar.service_account.Credentials"
        ".from_service_account_file",
        from_file,
    )
    monkeypatch.setattr("leistungsbot.google_calendar.build", build)

    calendar = GoogleCalendar(CALENDAR_ID, "/nowhere/key.json")

    from_file.assert_called_once()
    assert from_file.call_args.args[0] == "/nowhere/key.json"
    assert calendar.service is build.return_value


def test_a_missing_key_file_is_not_swallowed(monkeypatch):
    monkeypatch.setattr(
        "leistungsbot.google_calendar.service_account.Credentials"
        ".from_service_account_file",
        MagicMock(side_effect=FileNotFoundError("/nowhere/key.json")),
    )

    with pytest.raises(FileNotFoundError):
        GoogleCalendar(CALENDAR_ID, "/nowhere/key.json")
