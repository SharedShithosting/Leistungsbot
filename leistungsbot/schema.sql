-- LeistungsBot schema.
--
-- Translated from the MariaDB schema this bot used until the move to SQLite:
--   int/bigint/smallint -> INTEGER      bit(1)      -> INTEGER, 0 or 1
--   varchar/text        -> TEXT         double(9,6) -> REAL
--   date                -> DATE         datetime    -> TIMESTAMP
--
-- DATE and TIMESTAMP are not SQLite storage classes; they are declared for
-- documentation and read back as `datetime.date` / `datetime.datetime` by
-- LeistungsDB.convert. Identifiers stay quoted because `key`, `left` and
-- `google-place-id` are either keywords or contain a hyphen.

CREATE TABLE IF NOT EXISTS "locations" (
  "key"             INTEGER PRIMARY KEY AUTOINCREMENT,
  "name"            TEXT    NOT NULL UNIQUE,
  "google-place-id" TEXT    NOT NULL,
  "visited"         INTEGER NOT NULL DEFAULT 0,
  "address"         TEXT    NOT NULL,
  "phone"           TEXT,
  "url"             TEXT    NOT NULL,
  "lng"             REAL    NOT NULL,
  "lat"             REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS "members" (
  "key"     INTEGER   PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER   NOT NULL UNIQUE,
  "chat_id" INTEGER   UNIQUE,
  "score"   INTEGER   NOT NULL DEFAULT 0,
  "joined"  TIMESTAMP NOT NULL,
  "left"    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "leistungstag" (
  "key"      INTEGER PRIMARY KEY AUTOINCREMENT,
  "location" INTEGER NOT NULL REFERENCES "locations" ("key"),
  "date"     DATE    NOT NULL,
  "poll_id"  INTEGER NOT NULL,
  "venue_id" INTEGER NOT NULL,
  "type"     INTEGER NOT NULL,
  "closed"   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS "leistungstag_location"
  ON "leistungstag" ("location");

CREATE TABLE IF NOT EXISTS "location_rating" (
  "key"      INTEGER PRIMARY KEY AUTOINCREMENT,
  "location" INTEGER NOT NULL REFERENCES "locations" ("key"),
  "member"   INTEGER NOT NULL REFERENCES "members" ("key"),
  "rating"   INTEGER NOT NULL,
  UNIQUE ("location", "member")
);

CREATE INDEX IF NOT EXISTS "location_rating_member"
  ON "location_rating" ("member");

CREATE TABLE IF NOT EXISTS "participants" (
  "key"    INTEGER PRIMARY KEY AUTOINCREMENT,
  "member" INTEGER NOT NULL REFERENCES "members" ("key"),
  "event"  INTEGER NOT NULL REFERENCES "leistungstag" ("key")
);

CREATE INDEX IF NOT EXISTS "participants_member"
  ON "participants" ("member");
CREATE INDEX IF NOT EXISTS "participants_event"
  ON "participants" ("event");

-- `row_number() over (...)` needs SQLite 3.25, which every supported python
-- ships. MariaDB's timestamp(date, time) becomes datetime() over the
-- concatenated strings.

CREATE VIEW IF NOT EXISTS "events" AS
SELECT
  datetime("leistungstag"."date" || ' 19:00:00') AS "start",
  datetime("leistungstag"."date" || ' 22:00:00') AS "end",
  "leistungstag"."type"                          AS "type",
  "leistungstag"."closed"                        AS "closed",
  "leistungstag"."location"                      AS "location"
FROM "leistungstag"
JOIN "locations" "l" ON "leistungstag"."location" = "l"."key";

CREATE VIEW IF NOT EXISTS "leistungs_view" AS
SELECT
  row_number() OVER (ORDER BY "date") AS "number",
  "key", "location", "date", "poll_id", "venue_id", "type", "closed"
FROM "leistungstag"
WHERE "type" = 1;

CREATE VIEW IF NOT EXISTS "konkurrenz_view" AS
SELECT
  row_number() OVER (ORDER BY "date") AS "number",
  "key", "location", "date", "poll_id", "venue_id", "type", "closed"
FROM "leistungstag"
WHERE "type" = 2;

CREATE VIEW IF NOT EXISTS "zusatz_view" AS
SELECT
  row_number() OVER (ORDER BY "date") AS "number",
  "key", "location", "date", "poll_id", "venue_id", "type", "closed"
FROM "leistungstag"
WHERE "type" = 3;
