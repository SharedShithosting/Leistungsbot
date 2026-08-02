# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""LeistungsDB.dump - the SQL behind /backup.

The connection is faked instead of mocked: the stub answers the handful of
queries a dump makes, so the assertions are about the generated SQL and not
about which methods were called.
"""
from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal

import mysql.connector
import pytest
from mysql.connector.conversion import MySQLConverter

from leistungsbot.leistungs_db import DUMP_INCOMPLETE
from leistungsbot.leistungs_db import LeistungsDB

SHOW_TABLES = [
    ("locations", "BASE TABLE"),
    ("leistungstag", "BASE TABLE"),
    ("leistungs_view", "VIEW"),
]

CREATE_LOCATIONS = "CREATE TABLE `locations` (\n  `key` int(11) NOT NULL\n)"
CREATE_LEISTUNGSTAG = "CREATE TABLE `leistungstag` (\n  `key` int(11)\n)"
CREATE_VIEW = "CREATE VIEW `leistungs_view` AS SELECT 1"


class FakeCursor:
    """Answers exactly the queries LeistungsDB.dump sends."""

    def __init__(self, rows: dict[str, list[tuple]]):
        self.rows = rows
        self.result: list[tuple] = []
        self.description: list[tuple] = []
        self.queries: list[str] = []
        # views the user is not allowed to read the definition of
        self.deny_views: set[str] = set()

    def execute(self, sql, values=None):
        self.queries.append(sql)
        if sql.startswith("SHOW FULL TABLES"):
            self.result = SHOW_TABLES
            self.description = [("Tables_in_db",), ("Table_type",)]
        elif sql.startswith("SHOW CREATE TABLE"):
            table = sql.split("`")[1]
            create = {
                "locations": CREATE_LOCATIONS,
                "leistungstag": CREATE_LEISTUNGSTAG,
            }[table]
            self.result = [(table, create)]
        elif sql.startswith("SHOW CREATE VIEW"):
            view = sql.split("`")[1]
            if view in self.deny_views:
                raise denied(view)
            self.result = [(view, CREATE_VIEW)]
        elif sql.startswith("SELECT * FROM"):
            table = sql.split("`")[1]
            self.result = self.rows.get(table, [])
            self.description = [
                (name,) for name in COLUMNS.get(table, ["key"])
            ]
        else:
            raise AssertionError(f"unexpected query: {sql}")

    def fetchall(self):
        return self.result

    def fetchone(self):
        return self.result[0] if self.result else None


COLUMNS = {
    "locations": ["key", "name", "visited"],
    "leistungstag": ["key", "date"],
}


class FakeConnection:
    def __init__(self, rows):
        self.cursor_stub = FakeCursor(rows)

    def is_connected(self):
        return True

    def cursor(self, dictionary=False, buffered=False):
        return self.cursor_stub


@pytest.fixture
def real_db() -> LeistungsDB:
    """A LeistungsDB that talks to the stub instead of MySQL."""
    real_db = LeistungsDB.__new__(LeistungsDB)
    real_db.converter = MySQLConverter()
    real_db.mydb = FakeConnection(
        {
            "locations": [(1, "Bar A", True)],
            "leistungstag": [(10, date(2026, 8, 4))],
        },
    )
    return real_db


def test_tables_and_views_are_told_apart(real_db):
    tables, views = real_db.getTables()

    assert tables == ["leistungstag", "locations"]
    assert views == ["leistungs_view"]


def test_dump_starts_with_a_replayable_header(real_db):
    dump = real_db.dump()

    assert dump.startswith("-- LeistungsBot database dump\n-- created ")
    assert "SET NAMES utf8mb4;" in dump
    assert "SET FOREIGN_KEY_CHECKS = 0;" in dump
    assert dump.rstrip().endswith("SET FOREIGN_KEY_CHECKS = 1;")


def test_dump_contains_structure_and_contents(real_db):
    dump = real_db.dump()

    assert "DROP TABLE IF EXISTS `locations`;" in dump
    assert f"{CREATE_LOCATIONS};" in dump
    assert (
        "INSERT INTO `locations` (`key`, `name`, `visited`) "
        "VALUES (1, 'Bar A', 1);" in dump
    )
    assert (
        "INSERT INTO `leistungstag` (`key`, `date`) "
        "VALUES (10, '2026-08-04');" in dump
    )


def test_views_come_after_the_tables(real_db):
    dump = real_db.dump()

    assert "DROP VIEW IF EXISTS `leistungs_view`;" in dump
    assert f"{CREATE_VIEW};" in dump
    assert dump.index("`locations`") < dump.index("`leistungs_view`")


def test_empty_table_gets_no_insert(real_db):
    real_db.mydb.cursor_stub.rows = {"locations": [], "leistungstag": []}

    dump = real_db.dump()

    assert "INSERT INTO" not in dump
    assert f"{CREATE_LOCATIONS};" in dump


def denied(view: str) -> mysql.connector.Error:
    """What the server answers without the SHOW VIEW privilege."""
    return mysql.connector.errors.ProgrammingError(
        f"SHOW VIEW command denied to user 'leistungs_user'@'somewhere' "
        f"for table `leistungs_db`.`{view}`",
        errno=1142,
    )


def test_a_denied_view_does_not_cost_the_backup(real_db):
    real_db.mydb.cursor_stub.deny_views = {"leistungs_view"}

    dump = real_db.dump()

    # the data is still all there
    assert "INSERT INTO `locations`" in dump
    assert f"{CREATE_LOCATIONS};" in dump
    # and the view is accounted for rather than silently missing
    assert "-- view `leistungs_view` could not be dumped" in dump
    assert "CREATE VIEW `leistungs_view`" not in dump


def test_a_denied_view_marks_the_dump_incomplete(real_db):
    real_db.mydb.cursor_stub.deny_views = {"leistungs_view"}

    dump = real_db.dump()

    assert DUMP_INCOMPLETE in dump
    header = dump.split("SET NAMES")[0]
    assert (
        DUMP_INCOMPLETE in header
    ), "the warning has to be visible at the top"
    assert "SHOW VIEW command denied" in header


def test_a_complete_dump_is_not_marked(real_db):
    assert DUMP_INCOMPLETE not in real_db.dump()


def test_views_lose_their_definer_and_database(real_db):
    create = (
        "CREATE ALGORITHM=UNDEFINED DEFINER=`leistungs_user`@`%` "
        "SQL SECURITY DEFINER VIEW `leistungs_db`.`leistungs_view` AS "
        "select `leistungs_db`.`leistungstag`.`key` AS `key` "
        "from `leistungs_db`.`leistungstag`"
    )

    portable = real_db.portableView(create)

    assert "DEFINER=" not in portable
    assert "`leistungs_db`." not in portable
    assert portable.startswith("CREATE ALGORITHM=UNDEFINED SQL SECURITY")
    assert "VIEW `leistungs_view` AS" in portable
    assert "from `leistungstag`" in portable


def test_a_plain_view_survives_untouched(real_db):
    create = "CREATE VIEW `leistungs_view` AS select 1"

    assert real_db.portableView(create) == create


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "NULL"),
        (True, "1"),
        (False, "0"),
        (42, "42"),
        (1.5, "1.5"),
        (Decimal("4.25"), "4.25"),
        (b"\x01", "0x01"),
        (b"", "''"),
        (date(2026, 8, 4), "'2026-08-04'"),
        (datetime(2026, 8, 4, 19, 30), "'2026-08-04 19:30:00'"),
        ("Bar A", "'Bar A'"),
        ("it's", "'it\\'s'"),
        ("back\\slash", "'back\\\\slash'"),
    ],
)
def test_values_are_rendered_as_sql_literals(real_db, value, expected):
    assert real_db.sqlLiteral(value) == expected
