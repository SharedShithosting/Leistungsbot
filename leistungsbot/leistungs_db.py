# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The database, on SQLite.

One file, no server. The method names and return shapes are the ones the
rest of the bot already expects, so this is a swap of the storage engine and
not of the interface.

Two SQLite specifics worth knowing:

* dates are stored as ISO strings and read back as `datetime.date` /
  `datetime.datetime` by :meth:`LeistungsDB.convert`, because the callers do
  arithmetic and `strftime` on them
* foreign keys are off by default and have to be switched on per connection
"""

from __future__ import annotations

import logging
import re
import sqlite3
from datetime import date
from datetime import datetime
from enum import Enum
from enum import auto
from pathlib import Path

from leistungsbot import leistungs_config as lc
from leistungsbot.google_place import Places
from leistungsbot.leistungs_returns import LeistungsReturnCodes

SCHEMA = Path(__file__).parent / "schema.sql"

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?")

sqlite3.register_adapter(date, lambda value: value.isoformat())
sqlite3.register_adapter(datetime, lambda value: value.isoformat(sep=" "))


class LeistungsTagState(Enum):
    NONE = 0
    OPEN = 1
    CLOSED = 2


class Change(Enum):
    """! What happened to a leistungstag, for whoever is listening

    Announced by the four methods that write to the table. Closing a poll
    and moving a leistungstag to another location are both `UPDATED`: from
    the outside they are the same thing, a row that now says something else.
    """

    CREATED = auto()
    UPDATED = auto()
    REMOVED = auto()


class LeistungsDB:
    def __init__(self):
        self.google = Places()
        self.mydb = None
        #: Called with (`Change`, the leistungstag row) after every write to
        #: the table. The calendar sync is the reason this exists - see
        #: `leistungsbot.leistungs_calendar` - and the alternative was for
        #: every caller of `closeLeistungstag` to remember to say so.
        self.listeners: list = []
        self.connect()

    # ─────────────────────────────── listeners ──────────────────────────────

    def subscribe(self, listener) -> None:
        """! Hands `listener` every later change to the leistungstag table"""
        self.listeners.append(listener)

    def announce(self, change: Change, leistungstag: dict | None) -> None:
        """! Tells the listeners about one write

        Swallows whatever a listener raises. The write has already happened,
        and a calendar that is having a bad day must not turn a successful
        poll into a failed command.
        """
        if not leistungstag:
            return
        for listener in self.listeners:
            try:
                listener(change, leistungstag)
            except Exception:
                logging.exception(
                    "a listener failed on %s of leistungstag %s",
                    change.name.lower(),
                    leistungstag.get("key"),
                )

    # ────────────────────────────── connection ──────────────────────────────

    def path(self) -> Path:
        return Path(lc.config["sqlite"]["path"]).expanduser()

    def connect(self) -> bool:
        """! Opens the database, creating it from schema.sql if it is new"""
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self.mydb = sqlite3.connect(path, isolation_level=None)
            self.mydb.execute("PRAGMA foreign_keys = ON;")
            self.mydb.execute("PRAGMA journal_mode = WAL;")
            self.mydb.executescript(SCHEMA.read_text())
            return True
        except Exception as e:
            self.mydb = None
            logging.error("Error while opening the database: %s", e)
            return False

    def is_connected(self) -> bool:
        if self.mydb is None:
            return False
        try:
            self.mydb.execute("SELECT 1;")
            return True
        except sqlite3.Error:
            return False

    def cursor(self, dictionary: bool = False) -> sqlite3.Cursor:
        """! A cursor on a live connection

        Reconnects once if the connection went away, which is what every
        method used to do by hand.
        """
        if not self.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")
        self.mydb.row_factory = sqlite3.Row if dictionary else None
        return self.mydb.cursor()

    def checkConnection(self) -> bool:
        if self.is_connected():
            print("Connected to SQLite version ", sqlite3.sqlite_version)
            print("You're using database: ", self.path())
        return self.is_connected()

    def commit(self) -> None:
        # isolation_level=None means autocommit; kept so the call sites that
        # used to commit explicitly still read the same.
        pass

    # ─────────────────────────────── conversion ─────────────────────────────

    def convert(self, res, skinny_bitch=False):
        """! Normalises what SQLite hands back

        Rows become dicts or lists, and the ISO strings that dates are stored
        as become `date` / `datetime` again. `skinny_bitch` unwraps a
        one-element result, which is how the single value getters read.
        """
        if isinstance(res, sqlite3.Row):
            return {k: self.convert(res[k], skinny_bitch) for k in res.keys()}

        if not res:
            return None if res is None or res == [] or res == () else res

        if isinstance(res, dict):
            return {k: self.convert(v, skinny_bitch) for k, v in res.items()}

        if isinstance(res, (tuple, list)):
            res = [self.convert(i, skinny_bitch) for i in res]
            if skinny_bitch and len(res) == 1:
                return res[0]
            return res

        if isinstance(res, str):
            if TIMESTAMP.fullmatch(res):
                return datetime.fromisoformat(res)
            if DATE.fullmatch(res):
                return date.fromisoformat(res)

        return res

    # ──────────────────────────────── members ───────────────────────────────

    def addUser(self, user_id: int, chat_id: int = None):
        cursor = self.cursor()
        try:
            cursor.execute(
                'INSERT INTO "members" ("user_id", "chat_id", "score", '
                '"joined") VALUES (?, ?, ?, ?);',
                (user_id, chat_id, 0, datetime.now()),
            )
        except sqlite3.IntegrityError:
            cursor.execute(
                'UPDATE "members" SET "left" = ?, "chat_id" = ? '
                'WHERE "user_id" = ?;',
                (None, chat_id, user_id),
            )

    def getUsers(self):
        cursor = self.cursor()
        cursor.execute('SELECT * FROM "members";')
        return self.convert(cursor.fetchall())

    def getUserKey(self, user_id):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "key" FROM "members" WHERE "user_id" = ?;',
            (user_id,),
        )
        return self.convert(cursor.fetchone(), True)

    def getUserScore(self, user_id: int):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "score" FROM "members" WHERE "user_id" = ?;',
            (user_id,),
        )
        return self.convert(cursor.fetchone(), True)

    def setUserScore(self, user_id: int, score: int):
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "members" SET "score" = ? WHERE "user_id" = ?;',
            (score, user_id),
        )

    def increaseUserScore(self, user_id: int, value: int):
        self.setUserScore(user_id, self.getUserScore(user_id) + value)

    def removeUser(self, user_id: int):
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "members" SET "left" = ? WHERE "user_id" = ?;',
            (datetime.now(), user_id),
        )

    # ─────────────────────────────── locations ──────────────────────────────

    def addLocation(self, place_id: str, name: str) -> LeistungsReturnCodes:
        info = self.google.getPlaceInfo(place_id)
        cursor = self.cursor()
        retry = True
        orig_name = name
        cnt = 1
        res = LeistungsReturnCodes.OK
        while retry:
            try:
                cursor.execute(
                    'INSERT INTO "locations" ("name", "google-place-id", '
                    '"lat", "lng", "address", "phone", "url") '
                    "VALUES (?, ?, ?, ?, ?, ?, ?);",
                    (
                        name,
                        place_id,
                        info.get("geometry", {})
                        .get("location", {})
                        .get("lat", None),
                        info.get("geometry", {})
                        .get("location", {})
                        .get("lng", None),
                        info.get("formatted_address", None),
                        info.get("international_phone_number", None),
                        info.get("url", None),
                    ),
                )
                retry = False
            except sqlite3.IntegrityError:
                location = self.getLocationInfo(name)
                if location and location.get("google-place-id") == place_id:
                    retry = False
                    res = LeistungsReturnCodes.DB_DUPLICATE
                else:
                    cnt += 1
                    name = orig_name + str(cnt)
        return res

    def removeLocation(self, key):
        cursor = self.cursor()
        cursor.execute('DELETE FROM "locations" WHERE "key" = ?;', (key,))

    def getAllLocations(self):
        cursor = self.cursor()
        cursor.execute('SELECT "name" FROM "locations";')
        return self.convert(cursor.fetchall())

    def getLocationKey(self, location_name):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "key" FROM "locations" WHERE "name" = ?;',
            (location_name,),
        )
        return self.convert(cursor.fetchone(), True)

    def getLocationName(self, location_key):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "name" FROM "locations" WHERE "key" = ?;',
            (location_key,),
        )
        return self.convert(cursor.fetchone(), True)

    def getVisitedLocations(self):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "name", "key" FROM "locations" WHERE "visited" = 1;',
        )
        return self.convert(cursor.fetchall())

    def getVirgineLocations(self):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "name", "key" FROM "locations" WHERE "visited" = 0 '
            'ORDER BY "name" DESC;',
        )
        return self.convert(cursor.fetchall())

    def getLocationInfo(self, location_name):
        cursor = self.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM "locations" WHERE "name" = ?;',
            (location_name,),
        )
        return self.convert(cursor.fetchone(), True)

    def getLocationInfoByKey(self, key: int):
        cursor = self.cursor(dictionary=True)
        cursor.execute('SELECT * FROM "locations" WHERE "key" = ?;', (key,))
        return self.convert(cursor.fetchone(), True)

    def setLocationVisitedState(self, location_name, visited=True):
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "locations" SET "visited" = ? WHERE "name" = ?;',
            (int(visited), location_name),
        )

    def setLocationVisitedStateKey(self, location_key, visited=True):
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "locations" SET "visited" = ? WHERE "key" = ?;',
            (int(visited), location_key),
        )

    # ──────────────────────────────── ratings ───────────────────────────────

    def rateLocation(self, location_name, user_id, rating):
        self.rateLocationKey(
            self.getLocationKey(location_name),
            user_id,
            rating,
        )

    def rateLocationKey(self, location_key, user_id, rating):
        cursor = self.cursor()
        cursor.execute(
            'INSERT INTO "location_rating" ("location", "member", "rating") '
            "VALUES (?, ?, ?);",
            (location_key, self.getUserKey(user_id), rating),
        )

    def getAvgLocationRating(self, location_name):
        cursor = self.cursor()
        cursor.execute(
            'SELECT AVG("rating") FROM "location_rating" WHERE "location" = ?;',
            (self.getLocationKey(location_name),),
        )
        res = self.convert(cursor.fetchall(), skinny_bitch=True)
        return res if res else 0

    def getUserLocationRating(self, location_name, user_id):
        cursor = self.cursor(dictionary=True)
        cursor.execute(
            'SELECT "rating" FROM "location_rating" '
            'WHERE "location" = ? AND "member" = ?;',
            (self.getLocationKey(location_name), self.getUserKey(user_id)),
        )
        return self.convert(cursor.fetchone(), True)

    def getAvgUserLocationRating(self, user_id):
        cursor = self.cursor()
        cursor.execute(
            'SELECT AVG("rating") FROM "location_rating" WHERE "member" = ?;',
            (self.getUserKey(user_id),),
        )
        return self.convert(cursor.fetchall())

    # ────────────────────────────── leistungstag ────────────────────────────

    def addLeistungsTag(
        self,
        date: datetime,
        location_name: str,
        poll_id: int,
        venue_id: int,
        type: int,
    ) -> int:
        """! Writes a leistungstag down

        @returns The key of the new row, which is what the listeners are
                 told about and what a caller would otherwise have to look
                 up by poll id
        """
        cursor = self.cursor()
        cursor.execute(
            'INSERT INTO "leistungstag" ("location", "date", "poll_id", '
            '"venue_id", "type") VALUES (?, ?, ?, ?, ?);',
            (
                self.getLocationKey(location_name),
                date.date() if isinstance(date, datetime) else date,
                poll_id,
                venue_id,
                int(type),
            ),
        )
        key = cursor.lastrowid
        self.announce(Change.CREATED, self.getLeistungstag(key))
        return key

    def getLeistungstag(self, key: int):
        cursor = self.cursor(dictionary=True)
        cursor.execute('SELECT * FROM "leistungstag" WHERE "key" = ?;', (key,))
        return self.convert(cursor.fetchone(), True)

    def getLeistungstageByDate(self, date: date):
        cursor = self.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM "leistungstag" WHERE DATE("date") = ?;',
            (date,),
        )
        return self.convert(cursor.fetchall())

    def getLeistungsTagKeyPollId(self, poll_id: int):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "key" FROM "leistungstag" WHERE "poll_id" = ?;',
            (poll_id,),
        )
        return self.convert(cursor.fetchone(), True)

    def getOpenLeistungsTag(self, type: int = None):
        return self.getLeistungsTags(type, LeistungsTagState.OPEN)

    def getClosedLeistungsTag(self, type: int = None):
        return self.getLeistungsTags(type, LeistungsTagState.CLOSED)

    def closeLeistungstag(self, leistungstag_key: int):
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "leistungstag" SET "closed" = 1 WHERE "key" = ?;',
            (leistungstag_key,),
        )
        self.announce(Change.UPDATED, self.getLeistungstag(leistungstag_key))

    def removeLeistungstag(self, key: int):
        # read before the delete: the listeners are told which leistungstag
        # is gone, and afterwards there is nothing left to tell them about
        leistungstag = self.getLeistungstag(key)
        cursor = self.cursor()
        cursor.execute('DELETE FROM "leistungstag" WHERE "key" = ?;', (key,))
        self.announce(Change.REMOVED, leistungstag)

    def getHistory(self, type: int = None, limit: int = 100):
        cursor = self.cursor(dictionary=True)
        where = 'WHERE "type" = ?' if type else ""
        values = (int(type), int(limit)) if type else (int(limit),)
        cursor.execute(
            f'SELECT * FROM (SELECT * FROM "leistungstag" {where} '
            'ORDER BY "date" DESC LIMIT ?) ORDER BY "date";',
            values,
        )
        return self.convert(cursor.fetchall())

    def getHistoryCount(self, type: int = None):
        cursor = self.cursor()
        if type:
            cursor.execute(
                'SELECT COUNT(*) FROM "leistungstag" WHERE "type" = ?;',
                (int(type),),
            )
        else:
            cursor.execute('SELECT COUNT(*) FROM "leistungstag";')
        return self.convert(cursor.fetchone(), True)

    def getLatest(self, type: int = None, state=LeistungsTagState.NONE):
        results = self.getLeistungsTags(type, state, max_results=1)
        return results[0] if results else None

    def getLeistungsTags(
        self,
        type: int = None,
        state=LeistungsTagState.NONE,
        max_results: int = 0,
        before: datetime = None,
    ):
        conditions = []
        values: tuple = ()

        if before:
            conditions.append('"date" <= ?')
            values += (before,)
        if type:
            conditions.append('"type" = ?')
            values += (int(type),)
        if state != LeistungsTagState.NONE:
            conditions.append('"closed" = ?')
            values += (int(state == LeistungsTagState.CLOSED),)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        limit = ""
        if max_results > 0:
            limit = "LIMIT ?"
            values += (max_results,)

        cursor = self.cursor(dictionary=True)
        cursor.execute(
            f'SELECT * FROM "leistungstag" {where} ORDER BY "date" DESC '
            f"{limit};",
            values,
        )
        return self.convert(cursor.fetchall())

    def getMostRecentLeistungstag(self) -> dict:
        cursor = self.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM "leistungstag" ORDER BY "date" DESC LIMIT 1;',
        )
        return self.convert(cursor.fetchone(), True)

    def getLeistungstagByNumber(self, number: int) -> dict | None:
        cursor = self.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM "leistungs_view" WHERE "number" = ?;',
            (number,),
        )
        return self.convert(cursor.fetchone(), True)

    def switchLeistungstagLocation(
        self,
        lt_id: int,
        old_location_id: int,
        new_location_id: int,
    ) -> None:
        cursor = self.cursor()
        cursor.execute(
            'UPDATE "leistungstag" SET "location" = ? WHERE "key" = ?;',
            (new_location_id, lt_id),
        )
        cursor.execute(
            'UPDATE "locations" SET "visited" = '
            '(SELECT COUNT(*) > 0 FROM "leistungstag" WHERE "location" = ?) '
            'WHERE "key" = ?;',
            (old_location_id, old_location_id),
        )
        cursor.execute(
            'UPDATE "locations" SET "visited" = 1 WHERE "key" = ?;',
            (new_location_id,),
        )
        self.announce(Change.UPDATED, self.getLeistungstag(lt_id))

    # ────────────────────────────── participants ────────────────────────────

    def getParticipants(self, leistungstag_key: int):
        cursor = self.cursor()
        cursor.execute(
            'SELECT "member" FROM "participants" WHERE "event" = ?;',
            (leistungstag_key,),
        )
        return self.convert(cursor.fetchall())

    def getLatestParticipants(self, type=None):
        latest = self.getLatest(type)
        return self.getParticipants(latest["key"]) if latest else None

    def addParticipant(self, user_id: int, poll_id: int):
        cursor = self.cursor()
        cursor.execute(
            'INSERT INTO "participants" ("member", "event") VALUES (?, ?);',
            (
                self.getUserKey(user_id),
                self.getLeistungsTagKeyPollId(poll_id),
            ),
        )

    # ──────────────────────────────── backup ────────────────────────────────

    def getTables(self) -> tuple[list[str], list[str]]:
        """! Base table names and view names, each sorted by name"""
        cursor = self.cursor()
        cursor.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;",
        )
        tables = []
        views = []
        for name, kind in cursor.fetchall():
            (views if kind == "view" else tables).append(name)
        return tables, views

    def dump(self) -> str:
        """! The whole database as a SQL script

        `iterdump` walks structure and contents in an order that replays into
        an empty database, so unlike the MariaDB version there is nothing to
        assemble by hand and no privilege that can make it incomplete.

        @returns The dump as a single SQL script
        """
        if not self.is_connected():
            if not self.connect():
                raise Exception("No connection to DataBase available")

        lines = [
            "-- LeistungsBot database dump",
            f"-- created {datetime.now().isoformat(timespec='seconds')}",
            f"-- sqlite {sqlite3.sqlite_version}",
            "",
        ]
        lines += list(self.mydb.iterdump())
        lines.append("")
        return "\n".join(lines)

    def snapshot(self, target: Path) -> Path:
        """! Writes a consistent copy of the database to `target`

        `VACUUM INTO` takes the copy inside a transaction, so it is safe to
        run while the bot is working, and the result is a plain database file
        that can be opened directly.

        @param target Where to write the copy, must not exist yet

        @returns The path that was written
        """
        if not self.is_connected():
            if not self.connect():
                raise Exception("No connection to DataBase available")

        target = Path(target)
        target.unlink(missing_ok=True)
        self.mydb.execute("VACUUM INTO ?;", (str(target),))
        return target


if __name__ == "__main__":
    logging.basicConfig(filename="myapp.log", level=logging.DEBUG)
    db = LeistungsDB()
    db.checkConnection()
    print(db.getOpenLeistungsTag())
