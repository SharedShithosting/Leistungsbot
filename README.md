# Leistungsbot

[![unittests](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/unittests.yml/badge.svg)](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/unittests.yml)
[![integrationtests](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/integrationtests.yml/badge.svg)](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/integrationtests.yml)
[![tests](https://sharedshithosting.github.io/Leistungsbot/reports/badges/tests-badge.svg)](https://sharedshithosting.github.io/Leistungsbot/reports.html)
[![coverage](https://sharedshithosting.github.io/Leistungsbot/reports/badges/coverage-badge.svg)](https://sharedshithosting.github.io/Leistungsbot/reports/coverage/)
[![Docker Image CI](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/docker-image.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/SharedShithosting/Leistungsbot/main.svg)](https://results.pre-commit.ci/latest/github/SharedShithosting/Leistungsbot/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A telegram bot that organises a *leistungstag*: one group chat, one pub, one
poll asking who is coming. It looks the pub up on google places so nobody has
to type an address, keeps the guest list in a database, and remembers where
the group has already been so the next suggestion can be somewhere new.

Written for one chat in particular, in dialect, and it shows.


## What it does

A leistungstag has a short life, and a command for every step of it:

* an admin runs `/leistungspoll`, picks a location and a date. The bot
  searches google places, shows what it found and asks for a yes before it
  publishes anything.
* the poll goes to the leistungschat, pinned, and the leistungstag is written
  to the database with the location, the date and the poll it belongs to.
* `/sendreminder` nudges the chat, `/switcheroo` moves the evening to another
  pub, `/closepoll` ends it and `/purge` deletes it entirely.
* afterwards `/rate_location` records what the pub was worth and `/history`
  looks back at what has already happened.

Three kinds of leistungstag exist - the normal one, the *konkurrenz* poll and
the *zusatz* poll - which is what `/konkurrenzpoll` and `/zusatzpoll` create.

Locations are a list of their own: `/add_location` puts a pub forward,
`/show_locations` is everything nobody has been to yet, `/remove_location`
takes one back off the list.

A scheduler does the routine part without being asked - a reminder at noon,
the reservation message on monday, closing the previous poll at seven, and a
copy of the database to the backup chat on sunday morning.

`/help` lists the commands the sender is actually allowed to run: public,
admin of the leistungschat, or one of the `usernames` from the config.
`leistungsbot/Commands.py` is where that list lives, and it is the same list
telegram is given for its command menu.


## Running it

The container is the intended way. It needs a config file and a volume for
the database:

```bash
cp BotConfig.example BotConfig.yml   # then fill it in, see below
docker compose up -d
```

Or from PyPI, if you would rather run it next to something else:

```bash
pip install leistungsbot
LEISTUNGSBOT_CONFIG_FILE=BotConfig.yml python -m leistungsbot
```

The same line works from a checkout. There is a `leistungsbot` console
script as well, but it points at a `main` that `leistungsbot/__main__.py`
does not export - use `python -m` until that is fixed.


## Configuration

`BotConfig.example` is a complete file with fake values in it. The keys that
have to be set:

| key | what it is |
| --- | --- |
| `bot_token` | the token [@BotFather](https://telegram.me/BotFather) gives you |
| `api_hash`, `api_id` | from <https://my.telegram.org> |
| `google` | a google places api key |
| `leistungschat_id` | the chat the polls are published in |
| `leistungsadmin_id` | the admin chat |
| `chat_id` | where errors are reported |
| `usernames` | who may run the maintenance commands |
| `sqlite.path` | the database file, `/data/leistungs_db.sqlite` in the image |
| `backupchat_id` | optional, where `/backup` sends the database |
| `calendar` | optional, see below |

Every key can also come from the environment, prefixed and with `__` for the
nesting - `LEISTUNGSBOT_BOT_TOKEN`, `LEISTUNGSBOT_SQLITE__PATH`.
`LEISTUNGSBOT_CONFIG_FILE` says which file to read; without it the config is
looked for in the platform's usual place. A handful of the keys have command
line flags as well, `python -m leistungsbot --help` lists them.


## Development

```bash
poetry install --with=dev
poetry run pytest
poetry run pre-commit install
```

`tests/` is mocked end to end - no database, no google, no telegram - which
is the suite `unittests.yml` runs on every pull request, on 3.11 and 3.14.
`integrationtests.yml` is the one that talks to the real services, so it
waits for an environment approval first. Both hold every file to 75%
coverage rather than the project as a whole: `tools/check_coverage.py` is
what fails a module that has no tests at all.

The [coverage report] is published on every push to main, next to the junit
xml and the ruff output - see
<https://sharedshithosting.github.io/Leistungsbot/reports.html>. Badges lag
by up to ten minutes: github serves README images through a cache.

[coverage report]: https://sharedshithosting.github.io/Leistungsbot/reports/coverage/


### Development database

The bot needs a database with something in it before most commands do
anything interesting. `tools/seed_dev_db.py` builds one full of invented
data - pubs that do not exist, telegram ids far below the range telegram
issues, and leistungstage spread around today so `/history`,
`/sendreminder` and the scheduler's reminder window all have something to
find:

```bash
python tools/seed_dev_db.py
LEISTUNGSBOT_SQLITE__PATH=$PWD/leistungs_db.dev.sqlite python -m leistungsbot
```

The same seed always produces the same database, so `--seed 7` gives a
different but equally repeatable set.

To look inside it, `docker compose --profile dev up` starts a SQLite
browser on <https://localhost:3001>.


## Calendar

The bot can keep a calendar in step with the leistungstage: publishing one
creates an entry, closing the poll or moving it to another location updates
that entry, and purging it takes the entry away again. It hangs off the
database rather than off the commands, so the scheduler closing a poll on
its own counts too.

At every start the bot also walks the whole `leistungstag` table into the
calendar, oldest first and in a background thread. That is what gets the
leistungstage that predate the calendar in there, and it is safe to
repeat - an entry is identified by the leistungstag it belongs to, so it
is written over rather than duplicated. It reads the calendar once and
then writes only what is missing or says something else, so the usual
start costs a single request. The writes that are left are paced -
google answers a burst of them with "Rate Limit Exceeded" - and five
refusals in a row leave the rest for the next start.

Off unless configured, which is the `calendar` section:

```yaml
calendar:
  provider: "google"
  calendar_id: "abc123@group.calendar.google.com"
  credentials: "/data/google-service-account.json"
  timezone: "Europe/Vienna"
```

`timezone` may be left out, in which case the container's `TZ` decides and
`Europe/Vienna` is the last word. Times go into the calendar as wall clock
plus that zone, so a leistungstag stays at seven in the evening across a
daylight saving change.

`credentials` is the json key of a google [service account] - a bot has
nobody to click through a consent screen. The service account cannot make a
calendar for itself, so make one and share it with the account's email
address as "make changes to events".

Google is the only provider so far. `leistungsbot/leistungs_calendar.py` is
the part that does not know that: a second one is a `Calendar` subclass and
a line in `from_config`.

[service account]: https://cloud.google.com/iam/docs/service-account-overview


## License

Beerware, revision 42. See [LICENSE.md](LICENSE.md).
