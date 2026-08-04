# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""What the bot leaves behind in the temp directory.

The `app` fixture points `helper.temp_dir` at a tmp_path, so everything
written here is visible to the test and to nobody's real /tmp.

Two different things live in there:

* the database snapshot `/backup` sends, which is cleaned up
* the pickled scratch files behind the inline buttons, which used to be
  cleaned up only when the user walked a workflow all the way to its final
  button - #97
"""

from __future__ import annotations

import os
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from leistungsbot.BotHelper import SCRATCH_MAX_AGE
from tests import support


def temp_files(app) -> list[Path]:
    return sorted(Path(app.helper.temp_dir).iterdir())


def scratch_files(app) -> list[Path]:
    return [p for p in temp_files(app) if p.name.endswith("_leistung")]


# --- the backup, which does clean up after itself -----------------------


def test_the_backup_leaves_nothing_behind(app):
    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    assert app.bot.send_document.called
    assert temp_files(app) == []


def test_the_backup_was_actually_sent_from_a_file(app):
    support.send_command(app, "/backup")

    assert support.sent_documents(app), "no document reached telegram"


def test_the_snapshot_is_removed_even_when_sending_fails(app):
    app.bot.send_document.side_effect = RuntimeError("telegram said no")

    support.send_command(app, "/backup")

    assert temp_files(app) == [], "a failed send left the snapshot behind"


# --- the pickled scratch files ------------------------------------------


def test_a_finished_search_cleans_up(app):
    """The happy path: search, approve, add. `add_location` loads and
    deletes."""
    support.send_command(app, "/add_location")
    support.send_command(app, "Some Unknown Bar")

    rand_id = support.callback_payloads(support.last_markup(app))[0][
        "🍻search"
    ]
    support.press(app, {"🍻search": rand_id})
    support.press(app, {"🍻select": rand_id})

    assert scratch_files(app) == []


def test_an_abandoned_search_cleans_up(app):
    support.send_command(app, "/add_location")
    support.send_command(app, "Some Unknown Bar")

    assert scratch_files(app), "nothing was written, test proves nothing"

    support.send_command(app, "/cancel")

    assert scratch_files(app) == []


def test_a_rejected_dry_run_cleans_up(app):
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Bar A")
    date_str = support.callback_payloads(support.last_markup(app))[0][
        "🍻poll_date"
    ]
    support.press(app, {"🍻poll_date": date_str})

    assert scratch_files(app), "nothing was written, test proves nothing"

    support.press(app, {"🍻cancel": None})

    assert scratch_files(app) == []


def test_a_search_that_finds_nothing_cleans_up(app, google):
    """No results means no buttons, so nothing would ever consume it."""
    google.findPlace.return_value = []

    support.send_command(app, "/add_location")
    support.send_command(app, "Some Unknown Bar")

    assert scratch_files(app) == []


def test_cancelling_only_touches_the_senders_files(app):
    """Two people searching at once, one gives up."""
    other = 4004
    support.send_command(app, "/add_location")
    support.send_command(app, "Some Unknown Bar")
    support.send_command(app, "/add_location", user_id=other)
    support.send_command(app, "Another Bar", user_id=other)

    assert len(scratch_files(app)) == 2

    support.send_command(app, "/cancel")

    assert len(scratch_files(app)) == 1


# --- what earlier runs left behind --------------------------------------
#
# The cancel paths above need a message to arrive. Nothing arrives from the
# user who simply stops answering, and the ids are not remembered across a
# restart either, so the temp directory gets a pass at startup.


def age(path: Path, delta: timedelta) -> None:
    when = (datetime.now() - delta).timestamp()
    os.utime(path, (when, when))


def test_the_sweep_takes_a_stale_scratch_file(app):
    rand_id = app.helper.store_to_rand_file(["abandoned"])
    age(Path(app.helper.get_full_temp_file(rand_id)), SCRATCH_MAX_AGE * 2)

    assert app.sweep_scratch_files() == 1
    assert scratch_files(app) == []


def test_the_sweep_leaves_a_fresh_one_alone(app):
    """An inline button stays pressable, so a recent file is still in use."""
    app.helper.store_to_rand_file(["in flight"])

    assert app.sweep_scratch_files() == 0
    assert len(scratch_files(app)) == 1


def test_the_sweep_leaves_other_peoples_files_alone(app):
    """The temp directory belongs to the whole system, not to the bot."""
    stranger = Path(app.helper.temp_dir) / "somebody-elses.txt"
    stranger.write_text("not ours")
    age(stranger, SCRATCH_MAX_AGE * 2)

    app.sweep_scratch_files()

    assert stranger.exists()


def test_the_sweep_is_fine_with_an_empty_directory(app):
    assert app.sweep_scratch_files() == 0
