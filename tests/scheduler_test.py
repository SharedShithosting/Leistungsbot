# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The jobs that run on a timer, without waiting for the timer.

`Scheduler` had no tests at all, which is how it shipped registering a job
for a method that did not exist - every start of the bot died with
`AttributeError: 'Scheduler' object has no attribute 'send_backup'` before
it ever reached telegram. `test_every_scheduled_job_is_callable` is the
guard for that whole class of mistake; the rest drive the jobs directly.

The background thread is not started here: `run_continuously` is patched
out, because a real one would keep ticking through the rest of the suite.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
import schedule as schedule_module

from leistungsbot import leistungs_config as lc
from leistungsbot.BotScheduler import Scheduler
from tests import support


@pytest.fixture
def scheduler(monkeypatch, db):
    """A Scheduler with its jobs registered but no thread running."""
    # the schedule module keeps its jobs in a module level singleton, so a
    # second Scheduler would otherwise inherit the first one's
    schedule_module.clear()
    monkeypatch.setattr(
        Scheduler, "run_continuously", lambda self: MagicMock()
    )

    helper = MagicMock(name="helper")
    helper.db = db
    scheduler = Scheduler(MagicMock(name="bot"), helper)
    yield scheduler
    schedule_module.clear()


def leistungstag(date, poll_id=555, location=1, key=1):
    return {"date": date, "poll_id": poll_id, "location": location, "key": key}


# --- the registration itself -------------------------------------------


def test_every_scheduled_job_is_callable(scheduler):
    """The bug that started this file: a job pointing at nothing."""
    for job in scheduler.schedule.get_jobs():
        assert callable(job.job_func)


def test_every_scheduled_job_belongs_to_the_scheduler(scheduler):
    for job in scheduler.schedule.get_jobs():
        # schedule wraps the callable in a functools.partial and runs
        # update_wrapper over it, which copies __name__ but not __self__
        bound = getattr(job.job_func, "func", job.job_func)
        assert (
            getattr(bound, "__self__", None) is scheduler
        ), f"{job.job_func} is not a method of the Scheduler"


def test_the_expected_jobs_are_registered(scheduler):
    names = {job.job_func.__name__ for job in scheduler.schedule.get_jobs()}
    assert names == {
        "send_reminder",
        "send_reservation",
        "close_previous",
        "send_backup",
    }


# --- send_reminder ------------------------------------------------------


def test_reminder_goes_out_two_days_before(scheduler, db):
    in_two_days = (datetime.now() + timedelta(days=2)).date()
    db.getOpenLeistungsTag.return_value = [leistungstag(in_two_days)]

    scheduler.send_reminder()

    scheduler.bot.send_message.assert_called_once()
    args, kwargs = scheduler.bot.send_message.call_args
    assert args[0] == support.LEISTUNGSCHAT_ID
    assert "Übermorgen" in args[1]
    assert kwargs["reply_to_message_id"] == 555


@pytest.mark.parametrize("days", [0, 1, 3, 7])
def test_no_reminder_on_any_other_day(scheduler, db, days):
    when = (datetime.now() + timedelta(days=days)).date()
    db.getOpenLeistungsTag.return_value = [leistungstag(when)]

    scheduler.send_reminder()

    scheduler.bot.send_message.assert_not_called()


def test_no_open_leistungstag_is_quiet(scheduler, db):
    db.getOpenLeistungsTag.return_value = []

    scheduler.send_reminder()

    scheduler.bot.send_message.assert_not_called()


# --- send_reservation ---------------------------------------------------


def test_reservation_nag_goes_out_the_day_before(scheduler, db):
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    db.getClosedLeistungsTag.return_value = [leistungstag(tomorrow)]

    scheduler.send_reservation()

    scheduler.bot.forward_message.assert_called_once()
    said = scheduler.bot.send_message.call_args.args[1]
    assert "reserviert" in said


def test_reservation_nag_carries_the_phone_number(scheduler, db):
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    db.getClosedLeistungsTag.return_value = [leistungstag(tomorrow)]

    scheduler.send_reservation()

    said = scheduler.bot.send_message.call_args.args[1]
    assert "+43 1" in said


def test_no_reservation_nag_for_a_later_leistungstag(scheduler, db):
    later = (datetime.now() + timedelta(days=5)).date()
    db.getClosedLeistungsTag.return_value = [leistungstag(later)]

    scheduler.send_reservation()

    scheduler.bot.forward_message.assert_not_called()


# --- close_previous -----------------------------------------------------


def test_a_forgotten_leistungstag_is_closed(scheduler, db):
    db.getLeistungsTags.return_value = [leistungstag(datetime.now().date())]

    scheduler.close_previous()

    db.closeLeistungstag.assert_called_once_with(1)
    scheduler.bot.stop_poll.assert_called_once_with(
        support.LEISTUNGSCHAT_ID,
        555,
    )


def test_closing_tells_the_admins(scheduler, db):
    db.getLeistungsTags.return_value = [leistungstag(datetime.now().date())]

    scheduler.close_previous()

    args = scheduler.bot.send_message.call_args.args
    assert args[0] == support.LEISTUNGSADMIN_ID
    assert "Bar A" in args[1]


def test_nothing_to_close_is_quiet(scheduler, db):
    db.getLeistungsTags.return_value = []

    scheduler.close_previous()

    db.closeLeistungstag.assert_not_called()
    scheduler.bot.stop_poll.assert_not_called()


# --- send_backup --------------------------------------------------------


def test_backup_goes_to_the_configured_chat(scheduler, monkeypatch):
    monkeypatch.setitem(lc.config, "backupchat_id", -4242)

    scheduler.send_backup()

    scheduler.helper.send_backup.assert_called_once_with(-4242)


def test_no_backup_chat_means_no_backup(scheduler):
    """A deployment that never asked for this must not start posting its
    database somewhere."""
    assert not lc.config.get("backupchat_id")

    scheduler.send_backup()

    scheduler.helper.send_backup.assert_not_called()
