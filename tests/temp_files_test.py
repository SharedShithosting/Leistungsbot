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
* the pickled scratch files behind the inline buttons, which are cleaned up
  only when the user walks a workflow all the way to its final button
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


# --- the pickled scratch files, which do not ----------------------------


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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "#97: store_to_rand_file is only undone by load_from_rand_file, so a "
        "search the user never approves stays in the temp directory for ever"
    ),
)
def test_an_abandoned_search_cleans_up(app):
    support.send_command(app, "/add_location")
    support.send_command(app, "Some Unknown Bar")

    assert scratch_files(app), "nothing was written, test proves nothing"

    support.send_command(app, "/cancel")

    assert scratch_files(app) == []


@pytest.mark.xfail(
    strict=True,
    reason=(
        "#97: the dry run pickle is only undone by publish_leistungstag, so "
        "saying no to the preview leaves it behind"
    ),
)
def test_a_rejected_dry_run_cleans_up(app):
    support.send_command(app, "/leistungspoll")
    support.send_command(app, "Bar A")
    date_str = support.callback_payloads(support.last_markup(app))[0][
        "🍻poll_date"
    ]
    support.press(app, {"🍻poll_date": date_str})

    assert scratch_files(app), "nothing was written, test proves nothing"

    support.press(app, {"🍻cancle": None})

    assert scratch_files(app) == []
