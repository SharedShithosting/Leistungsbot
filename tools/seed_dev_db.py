#!/usr/bin/env python3
# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Build a SQLite database full of made up data, for development.

    python tools/seed_dev_db.py                     # ./leistungs_db.dev.sqlite
    python tools/seed_dev_db.py /tmp/dev.sqlite
    python tools/seed_dev_db.py --seed 7            # a different, repeatable set

Point the bot at the result:

    LEISTUNGSBOT_SQLITE__PATH=$PWD/leistungs_db.dev.sqlite python -m leistungsbot

or open it in the browser from docker-compose:

    docker compose --profile dev up

The data is invented: Linz pubs that do not exist, telegram ids in the range
telegram never issues, and dates around today so `/sendreminder`, the
scheduler's two day window and `/history` all have something to find. It is
deliberately *not* a copy of anything real - the repository used to carry a
production dump under example_db/, which is exactly what this replaces.

Everything is generated from a fixed seed, so two people running this get
the same database and can talk about "leistungstag 3".
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "leistungsbot" / "schema.sql"


def as_date(value: date) -> str:
    """The format LeistungsDB stores dates in, see its register_adapter."""
    return value.isoformat()


def as_timestamp(value: datetime) -> str:
    """The format LeistungsDB stores timestamps in, sep=" " and all."""
    return value.isoformat(sep=" ")


# type column of leistungstag, mirroring BotHelper.LeistungsTyp
NORMAL, KONKURENZ, ZUSATZ = 1, 2, 3

# Invented. Real ones would make this a copy of the production data again.
PUBS = [
    ("Zum Durstigen Kranich", "Kranichgasse 4, 4020 Linz", 14.286, 48.306),
    ("Bierklause Hinterhaus", "Hinterhausweg 17, 4040 Linz", 14.291, 48.318),
    ("Gasthaus Zur Letzten Runde", "Ringstraße 2, 4020 Linz", 14.301, 48.299),
    ("Schankraum Kollektiv", "Fabrikweg 9, 4030 Linz", 14.275, 48.281),
    ("Die Blaue Stunde", "Donaulände 33, 4020 Linz", 14.294, 48.311),
    ("Kellerlokal Nummer Sechs", "Kellergasse 6, 4040 Linz", 14.288, 48.321),
    ("Wirtshaus Alte Schmiede", "Schmiedgasse 12, 4020 Linz", 14.279, 48.303),
    ("Craftbier Depot", "Lagerstraße 40, 4030 Linz", 14.268, 48.288),
    ("Zum Vergessenen Fass", "Fasslgasse 1, 4020 Linz", 14.297, 48.307),
    ("Beisl am Eck", "Eckstraße 55, 4040 Linz", 14.284, 48.316),
    ("Nachtschicht Bar", "Industriezeile 88, 4030 Linz", 14.312, 48.276),
    ("Stüberl Sonnenschein", "Sonnenweg 3, 4020 Linz", 14.283, 48.309),
]

# Telegram user ids are positive and nowhere near this low; group chat ids
# are negative. Both are obviously fake at a glance.
MEMBERS = [
    (1001, -100_100_1),
    (1002, -100_100_2),
    (1003, -100_100_3),
    (1004, -100_100_4),
    (1005, -100_100_5),
    (1006, None),
    (1007, None),
]


def tuesdays_around(today: date, past: int, future: int) -> list[date]:
    """`past` tuesdays before today and `future` after, oldest first."""
    tuesday = today - timedelta(days=(today.weekday() - 1) % 7)
    return [
        tuesday + timedelta(weeks=offset)
        for offset in range(-past, future + 1)
    ]


def build(path: Path, seed: int) -> dict[str, int]:
    rng = random.Random(seed)
    today = date.today()

    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(path)
    db.executescript(SCHEMA.read_text())

    counts: dict[str, int] = {}

    # --- locations ------------------------------------------------------
    # The last few stay unvisited, so /show_locations and the poll keyboard
    # have something to offer.
    for index, (name, address, lng, lat) in enumerate(PUBS):
        db.execute(
            'INSERT INTO "locations" '
            '("name", "google-place-id", "visited", "address", "phone",'
            ' "url", "lng", "lat") VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                name,
                f"fake-place-{index:03d}",
                1 if index < len(PUBS) - 4 else 0,
                address,
                f"+43 732 {rng.randint(100000, 999999)}",
                f"https://maps.example/{index:03d}",
                lng,
                lat,
            ),
        )
    counts["locations"] = len(PUBS)

    # --- members --------------------------------------------------------
    for user_id, chat_id in MEMBERS:
        db.execute(
            'INSERT INTO "members" ("user_id", "chat_id", "score", "joined")'
            " VALUES (?, ?, ?, ?)",
            (
                user_id,
                chat_id,
                rng.randint(0, 40),
                as_timestamp(
                    datetime.combine(
                        today - timedelta(days=rng.randint(200, 900)),
                        datetime.min.time(),
                    ),
                ),
            ),
        )
    counts["members"] = len(MEMBERS)

    # --- leistungstage --------------------------------------------------
    # Past ones closed, future ones open. One of the future dates is two
    # days out, which is what the scheduler's reminder looks for, and one is
    # tomorrow, which is what the reservation nag looks for.
    dates = tuesdays_around(today, past=10, future=3)
    visited = list(range(1, len(PUBS) - 3))
    for index, when in enumerate(dates, start=1):
        db.execute(
            'INSERT INTO "leistungstag" '
            '("location", "date", "poll_id", "venue_id", "type", "closed")'
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                rng.choice(visited),
                as_date(when),
                6000 + index,
                7000 + index,
                NORMAL if index % 5 else rng.choice([KONKURENZ, ZUSATZ]),
                1 if when < today else 0,
            ),
        )
    for offset, kind in ((1, NORMAL), (2, NORMAL)):
        db.execute(
            'INSERT INTO "leistungstag" '
            '("location", "date", "poll_id", "venue_id", "type", "closed")'
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                rng.choice(visited),
                as_date(today + timedelta(days=offset)),
                6900 + offset,
                7900 + offset,
                kind,
                0,
            ),
        )
    counts["leistungstag"] = len(dates) + 2

    # --- ratings and participants ---------------------------------------
    ratings = 0
    for location in visited:
        for member in rng.sample(
            range(1, len(MEMBERS) + 1),
            rng.randint(1, 4),
        ):
            db.execute(
                'INSERT OR IGNORE INTO "location_rating" '
                '("location", "member", "rating") VALUES (?, ?, ?)',
                (location, member, rng.randrange(0, 525, 25)),
            )
            ratings += 1
    counts["location_rating"] = ratings

    participants = 0
    for event in range(1, len(dates) + 1):
        for member in rng.sample(
            range(1, len(MEMBERS) + 1),
            rng.randint(2, 5),
        ):
            db.execute(
                'INSERT INTO "participants" ("member", "event")'
                " VALUES (?, ?)",
                (member, event),
            )
            participants += 1
    counts["participants"] = participants

    db.commit()
    db.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "path",
        nargs="?",
        default="leistungs_db.dev.sqlite",
        type=Path,
        help="where to write the database (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed, so the result is repeatable (default: %(default)s)",
    )
    args = parser.parse_args()

    counts = build(args.path, args.seed)

    print(f"wrote {args.path}")
    for table, count in counts.items():
        print(f"  {count:>4} {table}")
    print(f"\n  LEISTUNGSBOT_SQLITE__PATH={args.path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
