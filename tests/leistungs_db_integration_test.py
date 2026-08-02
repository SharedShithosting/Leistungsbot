# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/backup against a real MySQL server.

A dump nobody has ever restored is not a backup. These tests take the dump
`LeistungsDB.dump()` produces, replay it into a scratch database, and compare
the result table by table and row by row against the original.

Runs in the `pytest` workflow, which starts a MariaDB and loads
`example_db/leistung_db.sql` into it. Everywhere else the tests skip: they
need a reachable server, and the replay additionally needs credentials that
may create a database.
"""
from __future__ import annotations

import os

import mysql.connector
import pytest
from mysql.connector.conversion import MySQLConverter

from leistungsbot import leistungs_config as lc
from leistungsbot.leistungs_db import LeistungsDB

pytestmark = pytest.mark.integration

SCRATCH_DATABASE = "leistungs_db_backup_test"


def statements(dump: str) -> list[str]:
    """Split a dump into statements.

    Every statement the dump writes ends on a line terminated by `;`, and
    string literals are escaped, so no `;` inside a value can end a line.
    """
    result = []
    current: list[str] = []
    for line in dump.splitlines():
        if not line.strip() or line.startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            result.append("\n".join(current).rstrip().rstrip(";"))
            current = []
    return result


def table_contents(connection, table: str) -> list[tuple]:
    cursor = connection.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM `{table}`;")
    return cursor.fetchall()


def unavailable(what: str) -> None:
    """Skip, unless the environment insists that it must be available.

    The `pytest` workflow sets LEISTUNGSBOT_REQUIRE_DB, because it is the
    only place these tests can run - a silent skip there means they never
    run at all, which is how they got missed the first time.
    """
    if os.environ.get("LEISTUNGSBOT_REQUIRE_DB"):
        pytest.fail(f"LEISTUNGSBOT_REQUIRE_DB is set but {what}")
    pytest.skip(what)


@pytest.fixture(scope="module")
def live_db() -> LeistungsDB:
    """A LeistungsDB on the configured server, or a skip."""
    db = LeistungsDB.__new__(LeistungsDB)
    db.converter = MySQLConverter()
    try:
        reachable = db.connect() and db.mydb.is_connected()
    except Exception:
        reachable = False
    if not reachable:
        unavailable(
            "no mysql server reachable at "
            f"{lc.config['mysql']['host']}/{lc.config['mysql']['db']} "
            f"as {lc.config['mysql']['user']}",
        )
    return db


@pytest.fixture(scope="module")
def dump(live_db) -> str:
    return live_db.dump()


@pytest.fixture(scope="module")
def root_connection():
    """A connection that may create databases, or a skip.

    The CI workflow exports every secret into the environment, so the root
    password is available there under `MYSQL_ROOT`.
    """
    password = os.environ.get("MYSQL_ROOT")
    if not password:
        unavailable("MYSQL_ROOT is not set, cannot create a scratch database")

    connection = mysql.connector.connect(
        host=lc.config["mysql"]["host"],
        user="root",
        password=password,
        ssl_disabled=True,
    )
    cursor = connection.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{SCRATCH_DATABASE}`;")
    cursor.execute(f"CREATE DATABASE `{SCRATCH_DATABASE}`;")
    connection.database = SCRATCH_DATABASE
    yield connection
    cursor = connection.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{SCRATCH_DATABASE}`;")
    connection.close()


def test_the_server_has_the_expected_schema(live_db):
    tables, views = live_db.getTables()

    assert "leistungstag" in tables
    assert "locations" in tables
    assert "members" in tables
    assert "participants" in tables
    assert "location_rating" in tables
    assert "leistungs_view" in views


def test_dump_covers_every_table_and_view(live_db, dump):
    tables, views = live_db.getTables()

    for table in tables:
        assert f"DROP TABLE IF EXISTS `{table}`;" in dump
        assert f"CREATE TABLE `{table}`" in dump
    for view in views:
        assert f"DROP VIEW IF EXISTS `{view}`;" in dump


def test_dump_has_one_insert_per_row(live_db, dump):
    tables, _views = live_db.getTables()

    for table in tables:
        rows = len(table_contents(live_db.mydb, table))
        inserts = dump.count(f"INSERT INTO `{table}` (")
        assert inserts == rows, f"{table}: {inserts} inserts for {rows} rows"


def test_dump_replays_into_an_empty_database(dump, root_connection):
    cursor = root_connection.cursor()

    for statement in statements(dump):
        cursor.execute(statement)
    root_connection.commit()

    cursor.execute("SHOW FULL TABLES;")
    restored = {name for name, _type in cursor.fetchall()}
    assert "leistungstag" in restored
    assert "locations" in restored


def test_restored_contents_match_the_original(live_db, dump, root_connection):
    cursor = root_connection.cursor()
    for statement in statements(dump):
        cursor.execute(statement)
    root_connection.commit()

    tables, _views = live_db.getTables()
    for table in tables:
        original = table_contents(live_db.mydb, table)
        restored = table_contents(root_connection, table)
        assert restored == original, f"{table} differs after the restore"


def test_restored_views_read_from_the_restored_database(
    live_db,
    dump,
    root_connection,
):
    """A view must not point back at the database it was dumped from."""
    cursor = root_connection.cursor()
    for statement in statements(dump):
        cursor.execute(statement)
    root_connection.commit()

    _tables, views = live_db.getTables()
    assert views, "expected at least one view in the schema"
    for view in views:
        cursor.execute(f"SHOW CREATE VIEW `{view}`;")
        create = cursor.fetchone()[1]
        assert f"`{lc.config['mysql']['db']}`." not in create
        # and it has to actually be queryable
        cursor.execute(f"SELECT * FROM `{view}` LIMIT 1;")
        cursor.fetchall()


def test_the_dump_is_replayable_twice(dump, root_connection):
    """The DROP statements make a restore idempotent."""
    cursor = root_connection.cursor()

    for _ in range(2):
        for statement in statements(dump):
            cursor.execute(statement)
    root_connection.commit()
