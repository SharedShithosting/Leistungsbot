# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Google Calendar, behind `leistungs_calendar.Calendar`.

A thin wrapper: translate a `CalendarEvent` into the json the api wants, and
turn the two http answers that are not really errors into ordinary
outcomes - inserting an id that is already there, and deleting one that is
not.

Authenticated as a service account, because a bot has nobody to click
through a consent screen. Create one, download its json key, and share the
calendar with the account's email address as "make changes to events"; the
service account cannot create a calendar for itself.
"""

from __future__ import annotations

import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from leistungsbot.leistungs_calendar import Calendar
from leistungsbot.leistungs_calendar import CalendarEvent

#: Read and write events. The narrower `calendar.events` scope exists but is
#: not granted to service accounts on a shared calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

#: The id is already taken - by this very leistungstag, on a retry, or by
#: the deleted event a purged one left behind.
CONFLICT = 409
#: Nothing under that id. `410 Gone` is what a deleted event answers.
MISSING = (404, 410)


def status_of(error: HttpError) -> int | None:
    """! The http status behind an `HttpError`, if it carries one"""
    return getattr(getattr(error, "resp", None), "status", None)


class GoogleCalendar(Calendar):
    """! `leistungs_calendar.Calendar` against the google calendar api

    @param calendar_id The calendar to write to, its id or an email address
    @param credentials_file Path to the service account key
    @param service An already built api client, which is what the tests use
    """

    def __init__(
        self,
        calendar_id: str,
        credentials_file: str = None,
        service=None,
    ) -> None:
        self.calendar_id = calendar_id
        self.service = service or self.connect(credentials_file)

    @staticmethod
    def connect(credentials_file: str):
        """! An api client for the service account in `credentials_file`"""
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES,
        )
        # cache_discovery needs a writable cache directory and warns loudly
        # when it does not get one; the bot builds this once per process
        return build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

    def body(self, event: CalendarEvent) -> dict:
        """! `event` as the api's event resource

        The times go out without an offset, with the zone named next to
        them: a leistungstag is agreed on as a wall clock time, so it stays
        at seven in the evening across a daylight saving change.

        `status` is set explicitly so that updating an event that was
        deleted revives it instead of quietly staying cancelled.
        """
        return {
            "summary": event.summary,
            "location": event.location,
            "description": event.description,
            "status": "confirmed",
            "start": {
                "dateTime": event.start.isoformat(),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end.isoformat(),
                "timeZone": event.timezone,
            },
            **event.extra,
        }

    def insert(self, event: CalendarEvent) -> None:
        """! Creates the event, id and all. Raises on a conflict."""
        body = self.body(event)
        body["id"] = event.uid
        self.events().insert(
            calendarId=self.calendar_id,
            body=body,
        ).execute()

    def update(self, event: CalendarEvent) -> None:
        """! Writes over the event with `event.uid`. Raises when it is gone."""
        self.events().update(
            calendarId=self.calendar_id,
            eventId=event.uid,
            body=self.body(event),
        ).execute()

    def add_event(self, event: CalendarEvent) -> None:
        try:
            self.insert(event)
        except HttpError as error:
            if status_of(error) != CONFLICT:
                raise
            # the id is ours and derived from the leistungstag key, so the
            # thing in the way is this leistungstag: write over it
            logging.info("calendar: %s exists already, updating", event.uid)
            self.update(event)

    def update_event(self, event: CalendarEvent) -> None:
        try:
            self.update(event)
        except HttpError as error:
            if status_of(error) not in MISSING:
                raise
            # never made it into the calendar, or somebody deleted it there.
            # `insert` rather than `add_event`: a conflict here would send
            # the two of them back and forth
            logging.info("calendar: %s is not there, adding it", event.uid)
            self.insert(event)

    def remove_event(self, uid: str) -> None:
        try:
            self.events().delete(
                calendarId=self.calendar_id,
                eventId=uid,
            ).execute()
        except HttpError as error:
            if status_of(error) not in MISSING:
                raise
            logging.info("calendar: %s was already gone", uid)

    def events(self):
        """! The api's events collection

        One place to reach for it, so the three calls above read as the api
        docs do and the tests have a single seam to hold on to.
        """
        return self.service.events()
