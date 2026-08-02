# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The maintenance commands: /showIds, /stats, /botlogs, /backup.

All three of the first ones read a file out of the working directory, so
every test here runs in a tmp_path with the files it expects - otherwise
they would either pick up whatever is lying around in the repository or
report a FileNotFoundError into the chat.
"""

from __future__ import annotations

import pytest

from tests import support

STRANGER = "hackl"
GROUPS_FILE = "joined_groups.txt"
LOGS_FILE = "POLL_LOGS.txt"


@pytest.fixture
def workdir(monkeypatch, tmp_path):
    """Run in a directory holding the files these commands expect."""
    (tmp_path / GROUPS_FILE).write_text("-100 -200 -100\n-300\n")
    (tmp_path / LOGS_FILE).write_text("a log line\n")
    monkeypatch.chdir(tmp_path)
    return tmp_path


# --- /stats -------------------------------------------------------------


def test_stats_counts_the_groups(app, workdir):
    support.send_command(app, "/stats")

    support.assert_said(app, "Number of polls Made:")
    support.assert_no_dev_error(app)


def test_stats_is_refused_to_a_stranger(app, workdir):
    support.send_command(app, "/stats", username=STRANGER)

    support.assert_said(app, "You Are Not Allowed To Use This Command")


def test_stats_without_the_file_reports_instead_of_crashing(
    app,
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)  # no joined_groups.txt here

    support.send_command(app, "/stats")

    assert support.sent_texts(app), "the handler said nothing at all"


def test_groups_is_the_same_command(app, workdir):
    support.send_command(app, "/groups")

    support.assert_said(app, "Number of polls Made:")


# --- /botlogs -----------------------------------------------------------


def test_botlogs_sends_the_log_file(app, workdir):
    support.send_command(app, "/botlogs")

    assert app.bot.send_document.called
    support.assert_no_dev_error(app)


def test_botlogs_is_refused_to_a_stranger(app, workdir):
    support.send_command(app, "/botlogs", username=STRANGER)

    support.assert_said(app, "You Are Not Allowed For This Command")
    assert not app.bot.send_document.called


def test_botlogs_without_the_file_says_so(app, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no POLL_LOGS.txt here

    support.send_command(app, "/botlogs")

    support.assert_said(app, "Error:")


# --- /showIds -----------------------------------------------------------


def test_show_ids_is_refused_to_a_stranger(app, workdir):
    support.send_command(app, "/showIds", username=STRANGER)

    support.assert_said(app, "You Are Not Allowed To Use This Command")
    assert not app.bot.send_document.called


def test_show_ids_sends_the_group_list(app, workdir):
    """Used to be impossible: the file was opened with mode "r " - with a
    trailing space - which raises ValueError before touching the disk."""
    support.send_command(app, "/showIds")

    assert app.bot.send_document.called


def test_show_ids_does_not_report_an_invalid_mode(app, workdir):
    support.send_command(app, "/showIds")

    assert "invalid mode" not in " ".join(support.sent_texts(app))


def test_show_ids_without_the_file_reports_it(app, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no joined_groups.txt here

    support.send_command(app, "/showIds")

    assert support.sent_texts(app), "the failure went nowhere"


# --- /backup ------------------------------------------------------------


def test_backup_is_refused_to_a_pleb(pleb):
    support.send_command(pleb, "/backup")

    support.assert_said(pleb, "nicht für den Pöbel")
    assert not pleb.bot.send_document.called


def test_backup_announces_itself_first(app):
    support.send_command(app, "/backup")

    support.assert_said(app, "I grab da de Datenbank zaum")
