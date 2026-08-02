[![Tests Status](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/integrationtests.yml/reports/junit/junit-badge.svg?dummy=8484744)](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/integrationtests.yml/reports/junit/report.html)
[![Docker Image CI](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/SharedShithosting/Leistungsbot/actions/workflows/docker-image.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/SharedShithosting/Leistungsbot/main.svg)](https://results.pre-commit.ci/latest/github/SharedShithosting/Leistungsbot/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Development database

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
is written over rather than duplicated.

Off unless configured, which is the `calendar` section:

```yaml
calendar:
  provider: "google"
  calendar_id: "abc123@group.calendar.google.com"
  credentials: "/data/google-service-account.json"
  timezone: "Europe/Vienna"
```

`credentials` is the json key of a google [service account] - a bot has
nobody to click through a consent screen. The service account cannot make a
calendar for itself, so make one and share it with the account's email
address as "make changes to events".

Google is the only provider so far. `leistungsbot/leistungs_calendar.py` is
the part that does not know that: a second one is a `Calendar` subclass and
a line in `from_config`.

[service account]: https://cloud.google.com/iam/docs/service-account-overview


## Intro
  <body>This Is A Simple Bot To Create Poll In Channel and Groups <br> And Also This Is our First Project Too..


## Enter you tokens at these are very important VARS:
  Without fork you cant deploy so fork it and edit in [Bot.py#L22](https://github.com/BotsUniverse/poll-bot/blob/main/Bot.py#L22)

## DEVLOPERS
😎ROHITH [ROHITHADITYA](https://telegram.me/rohithaditya) <br> 😋PARVAT [PARVAT_R](https://telegram.me/Parvat_R)

## QUICK NOTES
**DONT FORGET TO JOIN [Venila Bots](https://telegram.me/venilabots)**

## LANUGUAGES
<br>
>> PY BOT API
<br>
>> PYTHON

## SUPPORT GROUP
<a href="https://t.me/venilabots"><img src="https://img.shields.io/badge/Join-Telegram%20Channel-blue.svg?logo=telegram"></a><br>
<a href="https://t.me/venilabots1"><img src="https://img.shields.io/badge/Join-Telegram%20Group-blue.svg?logo=telegram"></a><br>

## SIMLIFIED READ ME HERE

Read Me --> [SIMPLIFIED README](https://springreen.ga/pollbot-docs)<br>
### DEPLOY
 ## DEPLOY TO HEROKU <br>
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](http://springreen.ga/pollbot-docs/#getting_started)

 ## RUN IN TERMUX
```
git clone https://github.com/Botsuniverse/poll-bot
cd poll-bot
python3 Bot.py
```

 ## RUN IN PYDROID 3 <br>
    (x) Just Copy The Bot.py to pydroid and Simply Run it

 ## RUN IN YOUR LINUX VPS OR DESKTOP

```
sudo apt update
sudo apt upgrade
git clone https://github.com/Botsuniverse/poll-bot
python3 Bot.py
```

 ## RUN THIS IN WINDOWS TERMINAL

```bash
git clone https://github.com/BotsUniverse/poll-bot/
cd where_the_fuck_you_stored/poll-bot
py Bot.py
```
