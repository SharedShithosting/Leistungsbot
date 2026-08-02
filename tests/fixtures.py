# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Fixtures that build a ``LeistungsBot`` without database, google or network.

Everything that leaves the process is replaced:

* ``LeistungsDB``  -> ``MagicMock(spec=LeistungsDB)`` with useful defaults
* ``Places``       -> ``MagicMock(spec=Places)`` with useful defaults
* ``Scheduler``    -> ``MagicMock`` (it would start a background thread)
* the telegram api calls on the ``TeleBot`` instance -> ``MagicMock``

``set_state`` / ``get_state`` / ``delete_state`` stay real, they only touch
the in-memory state storage and are what the multi step commands are built on.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import DEFAULT
from unittest.mock import MagicMock

import pytest
from telebot.storage import StateMemoryStorage

from leistungsbot import leistungs_config as lc
from leistungsbot.BotHelper import LeistungsTyp
from leistungsbot.google_place import Openness
from leistungsbot.google_place import Places
from leistungsbot.leistungs_db import LeistungsDB
from tests import support

# Telegram api calls: everything that would hit the network.
_API_METHODS = {
    "send_message",
    "reply_to",
    "send_poll",
    "stop_poll",
    "send_venue",
    "send_animation",
    "send_document",
    "pin_chat_message",
    "unpin_chat_message",
    "delete_message",
    "forward_message",
    "answer_callback_query",
    "edit_message_text",
    "edit_message_reply_markup",
    "get_chat_member",
    "get_me",
}

SNAPSHOT = b"SQLite format 3\x00-- test snapshot"

POLL_MESSAGE_ID = 555
VENUE_MESSAGE_ID = 554

LOCATION_A = {
    "key": 1,
    "name": "Bar A",
    "google-place-id": "place-a",
    "lat": 48.3,
    "lng": 14.28,
    "address": "Adresse A",
    "phone": "+43 1",
    "url": "https://maps.example/a",
    "visited": False,
}

LOCATION_B = {
    "key": 2,
    "name": "Bar B",
    "google-place-id": "place-b",
    "lat": 48.4,
    "lng": 14.29,
    "address": "Adresse B",
    "phone": "+43 2",
    "url": "https://maps.example/b",
    "visited": False,
}

GOOGLE_CANDIDATES = [
    {
        "place_id": "place-a",
        "name": "Bar A",
        "formatted_address": "Adresse A",
    },
    {
        "place_id": "place-b",
        "name": "Bar B",
        "formatted_address": "Adresse B",
    },
]

GOOGLE_PLACE_INFO = {
    "place_id": "place-a",
    "name": "Bar A",
    "formatted_address": "Adresse A",
    "international_phone_number": "+43 1",
    "url": "https://maps.example/a",
    "geometry": {"location": {"lat": 48.3, "lng": 14.28}},
}


def make_leistungstag(
    key: int = 10,
    location: int = 1,
    poll_id: int = POLL_MESSAGE_ID,
    venue_id: int = VENUE_MESSAGE_ID,
    closed: int = 0,
    type: int = int(LeistungsTyp.NORMAL),
    date=None,
) -> dict:
    """One row of the ``leistungstag`` table, as the db layer returns it."""
    return {
        "key": key,
        "location": location,
        "date": date or datetime(2026, 8, 4, 19, 0),
        "poll_id": poll_id,
        "venue_id": venue_id,
        "closed": closed,
        "type": type,
    }


@pytest.fixture
def db() -> MagicMock:
    """Database double, pre-loaded with two locations and one leistungstag."""
    db = MagicMock(spec=LeistungsDB, name="LeistungsDB")
    locations = {
        LOCATION_A["name"]: LOCATION_A,
        LOCATION_B["name"]: LOCATION_B,
    }
    by_key = {LOCATION_A["key"]: LOCATION_A, LOCATION_B["key"]: LOCATION_B}

    db.getVirgineLocations.return_value = [
        (LOCATION_A["name"], LOCATION_A["key"]),
        (LOCATION_B["name"], LOCATION_B["key"]),
    ]
    db.getAllLocations.return_value = [[name] for name in locations]
    db.getLocationInfo.side_effect = lambda name: locations.get(name)
    db.getLocationInfoByKey.side_effect = lambda key: by_key.get(key)
    db.getLocationKey.side_effect = lambda name: locations.get(name, {}).get(
        "key",
    )
    db.getLocationName.side_effect = lambda key: by_key.get(key, {}).get(
        "name",
    )
    db.getAvgLocationRating.return_value = 4.0
    db.getHistoryCount.return_value = 41
    db.getHistory.return_value = [make_leistungstag()]
    db.getOpenLeistungsTag.return_value = [make_leistungstag()]
    db.getLeistungstag.side_effect = lambda key: make_leistungstag(key=key)
    db.getLeistungsTags.return_value = [make_leistungstag()]
    db.getLeistungstageByDate.return_value = [make_leistungstag()]
    db.getLeistungstagByNumber.side_effect = lambda number: make_leistungstag(
        key=number + 100,
    )

    def snapshot(target):
        Path(target).write_bytes(SNAPSHOT)
        return Path(target)

    db.snapshot.side_effect = snapshot
    db.addLocation.return_value = None
    return db


@pytest.fixture
def google() -> MagicMock:
    """Google places double: two hits, always open."""
    google = MagicMock(spec=Places, name="Places")
    google.findPlace.return_value = list(GOOGLE_CANDIDATES)
    google.getPlaceInfo.return_value = dict(GOOGLE_PLACE_INFO)
    google.checkOpenHours.return_value = (
        Openness.OPEN,
        "Dienstag: 17:00–02:00",
    )
    return google


@pytest.fixture
def app(monkeypatch, db, google, tmp_path):
    """A ``LeistungsBot`` wired to the doubles above.

    Extra attributes for convenience: ``app.db``, ``app.google``,
    ``app.bot`` (with mocked api calls).
    """
    from leistungsbot import Bot

    monkeypatch.setattr("leistungsbot.BotHelper.LeistungsDB", lambda: db)
    monkeypatch.setattr("leistungsbot.BotHelper.Places", lambda: google)
    monkeypatch.setattr(
        "leistungsbot.Bot.Scheduler",
        MagicMock(name="Scheduler"),
    )

    lb = Bot.LeistungsBot()

    # The pickle files behind the 🍻search / 🍻publish tokens: keep them out
    # of the real temp dir, the bot only deletes them on the happy path.
    lb.helper.temp_dir = str(tmp_path)

    # Run handlers on the calling thread so assertions are deterministic.
    lb.bot.threaded = False

    # pyTelegramBotAPI's default state storage is a mutable default argument
    # and therefore shared by every TeleBot ever created - give each test its
    # own, otherwise states leak from one test into the next.
    lb.bot.current_states = StateMemoryStorage()

    # Chronological log over all api calls - the individual mocks only know
    # their own order, which is not enough to tell which message came last.
    outbox: list[tuple[str, tuple, dict]] = []

    # Documents are sent from a file handle that the bot closes and deletes
    # right after, so their content has to be captured while it is being sent.
    documents: list[tuple[int, str | None, bytes]] = []

    def recorder(name):
        def record(*args, **kwargs):
            if name == "send_document" and len(args) > 1:
                document = args[1]
                if hasattr(document, "read"):
                    documents.append(
                        (
                            args[0],
                            kwargs.get("visible_file_name"),
                            document.read(),
                        ),
                    )
            outbox.append((name, args, kwargs))
            return DEFAULT  # keep the mock's own return_value

        return record

    for name in _API_METHODS:
        monkeypatch.setattr(
            lb.bot,
            name,
            MagicMock(name=name, side_effect=recorder(name)),
        )

    lb.bot.send_poll.return_value = MagicMock(message_id=POLL_MESSAGE_ID)
    lb.bot.send_venue.return_value = MagicMock(message_id=VENUE_MESSAGE_ID)
    lb.bot.get_chat_member.return_value = MagicMock(status="administrator")

    lb.db = db
    lb.google = google
    lb.outbox = outbox
    lb.documents = documents
    return lb


@pytest.fixture
def pleb(app):
    """Demote the sender: not an admin of the leistungschat."""
    app.bot.get_chat_member.return_value = MagicMock(status="member")
    return app


@pytest.fixture(autouse=True)
def _config_is_loaded():
    """Guard against a silently broken configuration in conftest."""
    assert lc.config is not None, "test configuration did not load"
    assert lc.config["leistungschat_id"] == support.LEISTUNGSCHAT_ID
    assert lc.config["chat_id"] == support.DEV_CHAT_ID
