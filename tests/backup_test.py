# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""/backup - send a dump of the database as a document. Admins only."""

from __future__ import annotations

import os
import re

from tests import support

DUMP = "-- LeistungsBot database dump\nSELECT 1;\n"


def test_pleb_is_rejected(pleb, db):
    support.send_command(pleb, "/backup")

    support.assert_said(pleb, "nicht für den Pöbel")
    db.dump.assert_not_called()
    pleb.bot.send_document.assert_not_called()


def test_backup_is_sent_as_a_document(app, db):
    db.dump.return_value = DUMP

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    db.dump.assert_called_once_with()
    chat_id, _name, content = support.sent_documents(app)[0]
    assert chat_id == support.GROUP_CHAT_ID
    assert content.decode("utf-8") == DUMP


def test_the_document_is_named_after_the_moment(app, db):
    db.dump.return_value = DUMP

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    _chat_id, name, _content = support.sent_documents(app)[0]
    assert re.fullmatch(r"leistungsbot-backup-\d{8}-\d{6}\.sql", name)


def test_the_user_is_told_that_it_takes_a_moment(app, db):
    db.dump.return_value = DUMP

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    support.assert_said(app, "I grab da de Datenbank zaum")


def test_the_dump_does_not_stay_on_disk(app, db, tmp_path):
    db.dump.return_value = DUMP

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    assert os.listdir(tmp_path) == []


def test_an_incomplete_dump_is_flagged_to_the_user(app, db):
    db.dump.return_value = (
        "-- LeistungsBot database dump\n"
        "-- WARNING: this dump is incomplete\n"
        "-- view `events` is missing: SHOW VIEW command denied\n"
        "SELECT 1;\n"
    )

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    app.bot.send_document.assert_called_once()
    caption = app.bot.send_document.call_args.kwargs["caption"]
    assert "NED vollständig" in caption


def test_a_complete_dump_is_not_flagged(app, db):
    db.dump.return_value = DUMP

    support.send_command(app, "/backup")

    support.assert_no_dev_error(app)
    caption = app.bot.send_document.call_args.kwargs["caption"]
    assert "NED vollständig" not in caption


def test_a_failing_dump_is_reported(app, db):
    db.dump.side_effect = RuntimeError("no connection to the database")

    support.send_command(app, "/backup")

    support.assert_said(app, "no connection to the database")
    app.bot.send_document.assert_not_called()
