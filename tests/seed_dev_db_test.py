# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The development database seeder.

The point of these is drift: the seeder writes dates as strings in the shape
`LeistungsDB` expects, and nothing else would notice if the two stopped
agreeing. So the database is built and then read back through the real
`LeistungsDB`, not through raw sqlite.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from datetime import datetime
from pathlib import Path

import pytest

from leistungsbot.leistungs_db import LeistungsDB
from leistungsbot.leistungs_db import LeistungsTagState

ROOT = Path(__file__).resolve().parent.parent


def load_seeder():
    """Import tools/seed_dev_db.py, which is a script rather than a module."""
    path = ROOT / "tools" / "seed_dev_db.py"
    spec = importlib.util.spec_from_file_location("seed_dev_db", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["seed_dev_db"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def seeder():
    return load_seeder()


@pytest.fixture
def seeded(seeder, tmp_path, monkeypatch):
    """A freshly seeded database, opened through the real LeistungsDB."""
    path = tmp_path / "dev.sqlite"
    counts = seeder.build(path, seed=42)

    monkeypatch.setitem(
        __import__(
            "leistungsbot.leistungs_config",
            fromlist=["config"],
        ).config,
        "sqlite",
        {"path": str(path)},
    )
    # LeistungsDB has no close(); the connection goes with the object, and
    # tmp_path takes the file. Same as tests/leistungs_db_test.py.
    return LeistungsDB(), counts


def test_it_writes_every_table(seeded):
    _, counts = seeded

    assert counts["locations"] > 0
    assert counts["members"] > 0
    assert counts["leistungstag"] > 0
    assert counts["location_rating"] > 0
    assert counts["participants"] > 0


def test_dates_come_back_as_dates(seeded):
    """The whole reason this file exists."""
    db, _ = seeded

    leistungstage = db.getLeistungsTags()

    assert leistungstage
    assert all(isinstance(lt["date"], date) for lt in leistungstage)


def test_there_are_open_and_closed_leistungstage(seeded):
    db, _ = seeded

    assert db.getLeistungsTags(state=LeistungsTagState.OPEN)
    assert db.getLeistungsTags(state=LeistungsTagState.CLOSED)


def test_there_is_something_to_poll_for(seeded):
    """/leistungspoll needs an unvisited location to offer."""
    db, _ = seeded

    assert db.getVirgineLocations()


def test_a_location_reads_back_whole(seeded):
    db, _ = seeded

    name = db.getVirgineLocations()[0][0]
    info = db.getLocationInfo(name)

    assert info["address"]
    assert info["url"]
    assert isinstance(info["lat"], float)
    assert isinstance(info["lng"], float)


def test_the_scheduler_would_find_its_two_day_reminder(seeded):
    """The seeder plants a leistungstag two days out on purpose."""
    db, _ = seeded
    from datetime import timedelta

    wanted = (datetime.now() + timedelta(days=2)).date()
    open_ones = db.getOpenLeistungsTag()

    assert any(lt["date"] == wanted for lt in open_ones)


def test_the_scheduler_would_find_its_reservation_nag(seeded):
    db, _ = seeded
    from datetime import timedelta

    wanted = (datetime.now() + timedelta(days=1)).date()
    open_ones = db.getOpenLeistungsTag()

    assert any(lt["date"] == wanted for lt in open_ones)


def test_the_same_seed_gives_the_same_database(seeder, tmp_path):
    first = tmp_path / "a.sqlite"
    second = tmp_path / "b.sqlite"

    seeder.build(first, seed=7)
    seeder.build(second, seed=7)

    assert first.read_bytes() == second.read_bytes()


def test_a_different_seed_gives_a_different_database(seeder, tmp_path):
    first = tmp_path / "a.sqlite"
    second = tmp_path / "b.sqlite"

    seeder.build(first, seed=7)
    seeder.build(second, seed=8)

    assert first.read_bytes() != second.read_bytes()


def test_rerunning_replaces_rather_than_appends(seeder, tmp_path):
    path = tmp_path / "dev.sqlite"

    first = seeder.build(path, seed=42)
    again = seeder.build(path, seed=42)

    assert first == again


def test_the_ids_are_obviously_not_real(seeder):
    """A reviewer should be able to tell at a glance that this is invented.

    Telegram user ids are far larger than this, so nothing here can be
    mistaken for a real person - which is the point, the repository used to
    ship a production dump instead.
    """
    assert all(user_id < 10_000 for user_id, _ in seeder.MEMBERS)
    assert all(
        chat_id is None or chat_id < 0 for _, chat_id in seeder.MEMBERS
    )
