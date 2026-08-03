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
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from leistungsbot.leistungs_calendar import Calendar
from leistungsbot.leistungs_calendar import CalendarEvent

#: Read and write events. The narrower `calendar.events` scope exists but is
#: not granted to service accounts on a shared calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

#: How often a request may be repeated before it is allowed to fail.
#:
#: The client turns this into a randomised exponential backoff over the
#: answers that mean "later" - 429, the 5xx family, and the 403s whose
#: reason is a rate limit. It only does that when it is asked to: the
#: default is zero retries, and the startup pass duly gave up on the first
#: "Rate Limit Exceeded" google answered.
RETRIES = 5

#: Events per page when reading the calendar. 2500 is the most the api
#: hands out at once, and the whole history of a group fits in one page.
PAGE_SIZE = 2500

#: What of an event is worth transferring. Everything this bot writes and
#: nothing else - without a mask the api sends the full resource, which is
#: some twenty fields per event that would be read and thrown away.
FIELDS = "nextPageToken,items(id,summary,location,description,start,end)"

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

    def execute(self, request):
        """! Runs one api request, backing off rather than giving up

        Every call goes through here, so none of them can forget to.
        """
        return request.execute(num_retries=RETRIES)

    def insert(self, event: CalendarEvent) -> None:
        """! Creates the event, id and all. Raises on a conflict."""
        body = self.body(event)
        body["id"] = event.uid
        self.execute(
            self.events().insert(calendarId=self.calendar_id, body=body),
        )

    def update(self, event: CalendarEvent) -> None:
        """! Writes over the event with `event.uid`. Raises when it is gone."""
        self.execute(
            self.events().update(
                calendarId=self.calendar_id,
                eventId=event.uid,
                body=self.body(event),
            ),
        )

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
            self.execute(
                self.events().delete(
                    calendarId=self.calendar_id,
                    eventId=uid,
                ),
            )
        except HttpError as error:
            if status_of(error) not in MISSING:
                raise
            logging.info("calendar: %s was already gone", uid)

    def existing_events(self) -> dict[str, CalendarEvent]:
        """! Every event in the calendar, by id

        One request for the lot - `events.list` hands out up to
        `PAGE_SIZE` at a time - so the startup pass can ask what is there
        instead of writing every leistungstag to find out.

        Deleted events are left out, which is the default: an id google
        still remembers deleting is not an entry anybody can see, and the
        pass has to write that one again.
        """
        events: dict[str, CalendarEvent] = {}
        page = None
        while True:
            answer = self.execute(
                self.events().list(
                    calendarId=self.calendar_id,
                    maxResults=PAGE_SIZE,
                    fields=FIELDS,
                    pageToken=page,
                ),
            )
            for item in answer.get("items", []):
                event = self.event_from(item)
                if event:
                    events[event.uid] = event
            page = answer.get("nextPageToken")
            if not page:
                return events

    def event_from(self, item: dict) -> CalendarEvent | None:
        """! One event resource as a `CalendarEvent`, if it is comparable

        `None` for an all day event: it has a `date` where this bot writes
        a `dateTime`, so it is nothing this bot put there and nothing it
        can compare against.
        """
        start = item.get("start", {})
        end = item.get("end", {})
        if "dateTime" not in start or "dateTime" not in end:
            return None

        return CalendarEvent(
            uid=item.get("id", ""),
            summary=item.get("summary", ""),
            # the api answers in the event's own zone, so dropping the
            # offset gives back the wall clock time that was written
            start=self.wall_clock(start["dateTime"]),
            end=self.wall_clock(end["dateTime"]),
            location=item.get("location", ""),
            description=item.get("description", ""),
            timezone=start.get("timeZone", ""),
        )

    @staticmethod
    def wall_clock(stamp: str) -> datetime:
        """! An RFC3339 stamp as the local time it reads as"""
        return datetime.fromisoformat(stamp).replace(tzinfo=None)

    def events(self):
        """! The api's events collection

        One place to reach for it, so the three calls above read as the api
        docs do and the tests have a single seam to hold on to.
        """
        return self.service.events()
