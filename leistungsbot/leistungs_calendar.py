# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The leistungstage, as entries in a calendar.

Nothing in here knows about google. `Calendar` is the three calls a backend
has to answer, `CalendarEvent` is what they are handed, and `CalendarSync`
turns a row of the `leistungstag` table into one of those events and keeps
the calendar in step with the database. The google implementation lives in
`leistungsbot.google_calendar`, and swapping it for a caldav one is a new
`Calendar` plus a line in `from_config`.

An event is identified by a uid the *bot* picks, derived from the
leistungstag key, rather than by an id the backend hands back. That way
nothing has to be stored alongside the leistungstag: an update or a delete
knows the uid from the key alone. See `event_uid` for what the string may
look like.
"""

from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import time
from datetime import timedelta

from leistungsbot import leistungs_config as lc
from leistungsbot.leistungs_db import Change

#: When a leistungstag starts and how long it lasts. The same evening the
#: `events` view in schema.sql describes, kept in one place on purpose:
#: the view is what a calendar *export* would use, this is what the live
#: sync uses, and the two disagreeing would be a bug nobody notices.
EVENT_START = time(19, 0)
EVENT_DURATION = timedelta(hours=3)

#: `leistungstag.type`, spelled the way the poll question spells it. Keyed
#: by the int rather than by `BotHelper.LeistungsTyp`, which would import
#: the bot into a module the bot imports.
TITLES = {
    1: "Leistungstag",
    2: "Konkurrenz Leistungstag",
    3: "Leistungstag Zusatztermin",
}

DEFAULT_TITLE = "Leistungstag"
DEFAULT_TIMEZONE = "Europe/Vienna"


def event_uid(leistungstag_key: int) -> str:
    """! The calendar's id for the leistungstag with `leistungstag_key`

    Lower case letters and digits only, no separator. Google requires ids to
    be base32hex - the characters `a` to `v` and `0` to `9`, at least five
    of them - and an id a backend rejects is worse than an ugly one. Every
    letter in "leistungstag" is within that range.
    """
    return f"leistungstag{leistungstag_key}"


@dataclass
class CalendarEvent:
    """! One entry in a calendar, in the terms every backend has

    `start` and `end` are naive: the wall clock time in `timezone`, which is
    how a leistungstag is agreed on ("Dienstag um sieben") and what the
    database stores.
    """

    uid: str
    summary: str
    start: datetime
    end: datetime
    location: str = ""
    description: str = ""
    timezone: str = DEFAULT_TIMEZONE
    #: Free form, for backends that can carry more than the fields above
    extra: dict = field(default_factory=dict)


class Calendar(ABC):
    """! What a calendar backend has to be able to do

    Three calls, all of them by uid, and all of them expected to be
    idempotent: the sync repeats itself whenever the database is written,
    and a leistungstag that is already in the calendar has to survive being
    added again.
    """

    @abstractmethod
    def add_event(self, event: CalendarEvent) -> None:
        """! Puts `event` into the calendar"""

    @abstractmethod
    def update_event(self, event: CalendarEvent) -> None:
        """! Brings the entry with `event.uid` up to date"""

    @abstractmethod
    def remove_event(self, uid: str) -> None:
        """! Takes the entry with `uid` out of the calendar

        An entry that is not there is not an error - the leistungstag it
        belonged to is gone either way.
        """


class CalendarSync:
    """! Keeps a `Calendar` in step with the `leistungstag` table

    Subscribed to `LeistungsDB`, so a leistungstag that is created, closed,
    moved or purged reaches the calendar without any handler having to
    remember to say so.

    Never raises. A calendar that is unreachable, misconfigured or simply
    slow must not take the bot down with it: the database write has already
    happened by the time this runs, and the poll in the chat is what the
    group actually goes by.
    """

    def __init__(self, calendar: Calendar, db, timezone: str = None) -> None:
        self.calendar = calendar
        self.db = db
        self.timezone = timezone or DEFAULT_TIMEZONE

    def on_change(self, change: Change, leistungstag: dict) -> None:
        """! Reacts to one write to the `leistungstag` table

        @param change What happened to it
        @param leistungstag The row, as it is after the write - and as it
               was just before it, for a row that has been deleted
        """
        try:
            if change is Change.REMOVED:
                self.calendar.remove_event(event_uid(leistungstag["key"]))
            elif change is Change.CREATED:
                self.calendar.add_event(self.event_for(leistungstag))
            else:
                self.calendar.update_event(self.event_for(leistungstag))
        except Exception:
            logging.exception(
                "calendar: %s of leistungstag %s failed",
                change.name.lower(),
                leistungstag.get("key"),
            )

    def backfill(self) -> int:
        """! Puts every leistungstag the database knows into the calendar

        @returns How many of them made it

        For the leistungstage that already existed when the calendar was
        configured: they were never announced, so nothing else would ever
        put them there. Oldest first, so a calendar that is being filled
        for the first time fills in the order the group lived it.

        Safe to repeat, which is why it can just run at every start: the
        uid comes from the leistungstag key, so an entry that is already
        there is written over rather than duplicated.

        One entry that cannot be written does not stop the rest - a single
        purged location or a rate limit would otherwise cost the whole
        history.
        """
        leistungstage = self.db.getLeistungsTags() or []
        done = 0
        failed = 0
        # getLeistungsTags hands them back newest first
        for leistungstag in reversed(leistungstage):
            try:
                self.calendar.add_event(self.event_for(leistungstag))
                done += 1
            except Exception:
                failed += 1
                logging.exception(
                    "calendar: could not sync leistungstag %s",
                    leistungstag.get("key"),
                )
        logging.info(
            "calendar: %s leistungstage synced, %s failed",
            done,
            failed,
        )
        return done

    def event_for(self, leistungstag: dict) -> CalendarEvent:
        """! The calendar entry a row of the `leistungstag` table describes"""
        info = self.db.getLocationInfoByKey(leistungstag["location"]) or {}
        start = datetime.combine(leistungstag["date"], EVENT_START)
        title = TITLES.get(leistungstag["type"], DEFAULT_TITLE)
        name = info.get("name", "")

        return CalendarEvent(
            uid=event_uid(leistungstag["key"]),
            summary=f"{title}: {name}" if name else title,
            start=start,
            end=start + EVENT_DURATION,
            location=info.get("address", ""),
            description=self.description(leistungstag, info),
            timezone=self.timezone,
        )

    def description(self, leistungstag: dict, info: dict) -> str:
        """! The body of the entry: how to reach the place, and the poll"""
        lines = [
            value for value in (info.get("phone"), info.get("url")) if value
        ]
        if not leistungstag["closed"]:
            lines.append("Die Abstimmung läuft noch.")
        return "\n".join(lines)


def from_config(db) -> CalendarSync | None:
    """! The configured calendar sync, or `None` when there is none

    Absent configuration is the normal case rather than an error: a bot that
    is not supposed to keep a calendar simply does not have the section, and
    every existing deployment is one of those.
    """
    settings = lc.config.get("calendar") if lc.config else None
    if not settings:
        return None

    calendar_id = settings.get("calendar_id")
    if not calendar_id:
        logging.warning("calendar: no calendar_id configured, not syncing")
        return None

    provider = (settings.get("provider") or "google").lower()
    if provider != "google":
        logging.warning("calendar: unknown provider %r, not syncing", provider)
        return None

    # imported here so the google client is only needed by a deployment that
    # actually syncs a calendar
    from leistungsbot.google_calendar import GoogleCalendar

    try:
        calendar = GoogleCalendar(calendar_id, settings.get("credentials"))
    except Exception:
        logging.exception("calendar: could not reach the calendar backend")
        return None

    return CalendarSync(calendar, db, settings.get("timezone"))
