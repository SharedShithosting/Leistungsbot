#!/usr/bin/env python3
"""Load a LeistungsBot MySQL dump into a fresh SQLite database.

    python tools/mysql_to_sqlite.py <mysql-dump.sql> <out.sqlite>

One-off migration off MariaDB. Only the INSERT statements are read from the
dump; the schema comes from leistungsbot/schema.sql, because MariaDB's
CREATE TABLE is not valid SQLite. Values are parsed with MySQL's quoting
rules, so escaped quotes and the `0x..` literals that `bit` columns are
dumped as survive the trip.

Works with a mysqldump as well as with a dump from the bot's own /backup,
as long as the INSERTs carry their column names.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

INSERT = re.compile(
    r"^INSERT INTO `(?P<table>[^`]+)` \((?P<columns>.+?)\) VALUES \((?P<values>.*)\);$",
)

# MySQL's string escapes, as produced by MySQLConverter.escape
UNESCAPE = {
    "0": "\0",
    "'": "'",
    '"': '"',
    "b": "\b",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "Z": "\x1a",
    "\\": "\\",
    "%": "%",
    "_": "_",
}


def unescape(text: str) -> str:
    out = []
    escaped = False
    for char in text:
        if escaped:
            out.append(UNESCAPE.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            out.append(char)
    return "".join(out)


def split_values(values: str) -> list[str]:
    """Split a VALUES body on commas that are not inside a string."""
    parts = []
    current = []
    in_string = False
    escaped = False
    for char in values:
        if in_string:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_string = False
        elif char == "'":
            in_string = True
            current.append(char)
        elif char == ",":
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return parts


def convert(token: str):
    if token == "NULL":
        return None
    if token.startswith("'") and token.endswith("'"):
        return unescape(token[1:-1])
    if token.lower().startswith("0x"):
        # `bit` columns arrive as hex; 0x00 / 0x01 become 0 / 1
        return int(token, 16)
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    return float(token)


def main() -> int:
    dump_path, out_path = (Path(a) for a in sys.argv[1:3])
    schema_path = Path(__file__).parent.parent / "leistungsbot" / "schema.sql"
    if out_path.exists():
        out_path.unlink()

    connection = sqlite3.connect(out_path)
    connection.executescript(schema_path.read_text())

    # Foreign keys off during the load: the dump is ordered alphabetically,
    # so leistungstag arrives before the locations it points at.
    connection.execute("PRAGMA foreign_keys = OFF;")

    counts: dict[str, int] = {}
    for line in dump_path.read_text().splitlines():
        match = INSERT.match(line)
        if not match:
            continue
        table = match.group("table")
        columns = [
            c.strip().strip("`") for c in match.group("columns").split(",")
        ]
        values = [convert(v) for v in split_values(match.group("values"))]
        placeholders = ", ".join("?" * len(values))
        quoted = ", ".join(f'"{c}"' for c in columns)
        connection.execute(
            f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders});',
            values,
        )
        counts[table] = counts.get(table, 0) + 1

    connection.commit()

    violations = connection.execute("PRAGMA foreign_key_check;").fetchall()
    if violations:
        print(f"FOREIGN KEY VIOLATIONS: {violations[:5]}")
        return 1

    for table in sorted(counts):
        stored = connection.execute(
            f'SELECT COUNT(*) FROM "{table}";',
        ).fetchone()[0]
        status = "ok" if stored == counts[table] else "MISMATCH"
        print(
            f"{table:16} {counts[table]:5} inserted  {stored:5} stored  {status}",
        )

    for view in ("events", "leistungs_view", "konkurrenz_view", "zusatz_view"):
        rows = connection.execute(
            f'SELECT COUNT(*) FROM "{view}";',
        ).fetchone()[0]
        print(f"{view:16} {rows:5} rows (view)")

    connection.execute("VACUUM;")
    connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
