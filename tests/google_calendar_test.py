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
