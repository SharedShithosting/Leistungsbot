# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Helper.report_error - the one place a failing command is reported.

The reporter must never raise. It used to be inlined in every handler, so a
stale chat id in the configuration made the reporter itself throw and the
original cause was lost - which is exactly how a /backup failure showed up
as "group chat was upgraded to a supergroup chat".
"""
from __future__ import annotations

from telebot.apihelper import ApiTelegramException

from tests import support

MIGRATED_TO = -1001234567890


def migration_error() -> ApiTelegramException:
    """What telegram answers when a group became a supergroup."""
    result_json = {
        "ok": False,
        "error_code": 400,
        "description": "Bad Request: group chat was upgraded to a supergroup chat",
        "parameters": {"migrate_to_chat_id": MIGRATED_TO},
    }
    return ApiTelegramException("sendMessage", "", result_json)


def dev_reports(app) -> list[tuple[int, str]]:
    """``(chat_id, text)`` of everything that went to the dev chat."""
    return [
        (args[0], args[1])
        for name, args, _ in app.outbox
        if name == "send_message" and len(args) > 1 and "Hi Devs" in args[1]
    ]


def test_the_user_and_the_devs_are_told(app):
    message = support.make_message("/backup")

    app.helper.report_error(message, RuntimeError("dump failed"))

    support.assert_said(app, "An error occurred!")
    chat_id, text = dev_reports(app)[0]
    assert chat_id == support.DEV_CHAT_ID
    assert "dump failed" in text
    assert "/backup" in text


def test_a_failing_dev_chat_does_not_hide_the_error(app):
    """The bug behind the /backup traceback: the reporter threw itself."""
    app.bot.send_message.side_effect = migration_error()
    message = support.make_message("/backup")

    app.helper.report_error(message, RuntimeError("the real cause"))

    # the user still hears about it, and nothing propagates
    reply = app.bot.reply_to.call_args.args[1]
    assert "the real cause" in reply


def test_a_failing_user_reply_does_not_stop_the_dev_report(app):
    app.bot.reply_to.side_effect = migration_error()
    message = support.make_message("/backup")

    app.helper.report_error(message, RuntimeError("the real cause"))

    app.bot.send_message.assert_called_once()
    assert "the real cause" in app.bot.send_message.call_args.args[1]


def test_both_channels_failing_is_survived(app):
    app.bot.reply_to.side_effect = migration_error()
    app.bot.send_message.side_effect = migration_error()

    app.helper.report_error(
        support.make_message("/backup"),
        RuntimeError("the real cause"),
    )


def test_a_supergroup_migration_names_the_new_id(app):
    app.helper.report_error(support.make_message("/backup"), migration_error())

    support.assert_said(app, "Supergruppe")
    support.assert_said(app, str(MIGRATED_TO))


def test_an_ordinary_error_gets_no_migration_hint(app):
    app.helper.report_error(
        support.make_message("/backup"),
        RuntimeError("dump failed"),
    )

    support.assert_not_said(app, "Supergruppe")


def test_migrated_chat_id_only_fires_for_migrations(app):
    assert app.helper.migrated_chat_id(migration_error()) == MIGRATED_TO
    assert app.helper.migrated_chat_id(RuntimeError("nope")) is None
    forbidden = ApiTelegramException(
        "sendMessage",
        "",
        {"error_code": 403, "description": "Forbidden: bot was kicked"},
    )
    assert app.helper.migrated_chat_id(forbidden) is None


def test_a_failing_command_reports_once(app, db):
    """End to end: the /backup handler routes through the reporter."""
    db.dump.side_effect = RuntimeError("no connection to the database")

    support.send_command(app, "/backup")

    reports = dev_reports(app)
    assert len(reports) == 1
    assert "no connection to the database" in reports[0][1]
