# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Starting up: the argument parser, the version string, the config.

`main` is the one path nothing else exercises, and it is where the crash
that started all this showed up - the bot died in `LeistungsBot()` before
reaching telegram.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from leistungsbot import Bot
from leistungsbot import _version
from leistungsbot import leistungs_config as lc


@pytest.fixture
def started(monkeypatch):
    """`main` with the bot itself replaced; returns the fake instance."""
    instance = MagicMock(name="LeistungsBot")
    monkeypatch.setattr(Bot, "LeistungsBot", lambda: instance)
    monkeypatch.setattr(Bot.lc, "set_args", MagicMock(name="set_args"))
    return instance


def run_main(monkeypatch, *argv):
    monkeypatch.setattr("sys.argv", ["leistungsbot", *argv])
    Bot.main()


# --- main ---------------------------------------------------------------


def test_main_publishes_the_commands_before_polling(monkeypatch, started):
    run_main(monkeypatch)

    started.publish_commands.assert_called_once()
    started.infinite_poll.assert_called_once()


def test_main_accepts_the_documented_flags(monkeypatch, started):
    run_main(
        monkeypatch,
        "--token",
        "123:abc",
        "--google",
        "key",
        "--chat",
        "-1",
        "--db",
        "/tmp/x.sqlite",
    )

    namespace = Bot.lc.set_args.call_args.args[0]
    assert namespace.bot_token == "123:abc"
    assert getattr(namespace, "sqlite.path") == "/tmp/x.sqlite"


def test_main_rejects_an_unknown_flag(monkeypatch, started):
    with pytest.raises(SystemExit):
        run_main(monkeypatch, "--definitely-not-a-flag")


def test_the_config_is_passed_with_dots(monkeypatch, started):
    run_main(monkeypatch)

    assert Bot.lc.set_args.call_args.kwargs["dots"] is True


# --- _version -----------------------------------------------------------


def test_the_version_is_a_string():
    assert isinstance(_version.__version__, str)
    assert _version.__version__


def test_the_version_tuple_starts_with_numbers():
    assert isinstance(_version.__version_tuple__, tuple)
    assert isinstance(_version.__version_tuple__[0], int)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1.3.0", (1, 3, 0)),
        ("2.0", (2, 0)),
        ("1.3.0.post2.dev0+abc1234", (1, 3, 0, "post2.dev0+abc1234")),
        ("1.3.0+abc1234.dirty", (1, 3, 0, "+abc1234.dirty")),
        ("1.3.0rc1", (1, 3, "0rc1")),
    ],
)
def test_a_version_string_becomes_a_tuple(text, expected):
    assert _version._as_tuple(text) == expected


def test_the_metadata_fallback_reads_the_distribution(monkeypatch):
    """Hermetic on purpose.

    Whether the venv records a real version depends on how it was installed
    - a plain `poetry install` can leave the 0.0.0 placeholder behind - so
    the fallback is fed its input rather than asked to find one.
    """
    monkeypatch.setattr(
        "importlib.metadata.version",
        lambda _name: "1.3.0.post2.dev0+abc1234",
    )

    text, parts = _version._from_metadata()

    assert text == "1.3.0.post2.dev0+abc1234"
    assert parts == (1, 3, 0, "post2.dev0+abc1234")


def test_the_placeholder_is_not_treated_as_a_version(monkeypatch):
    """0.0.0 means substitution never ran, not "version zero"."""
    monkeypatch.setattr("importlib.metadata.version", lambda _name: "0.0.0")

    assert _version._from_metadata() is None


def test_the_fallback_gives_up_on_an_uninstalled_package(monkeypatch):
    def missing(_name):
        from importlib.metadata import PackageNotFoundError

        raise PackageNotFoundError

    monkeypatch.setattr("importlib.metadata.version", missing)

    assert _version._from_metadata() is None


# --- config -------------------------------------------------------------


def test_the_test_config_is_loaded():
    assert lc.config is not None
    assert lc.config["bot_token"] == "123456:TEST-TOKEN"


def test_the_backup_chat_is_optional():
    """It has to stay optional, or an existing deployment would start
    posting its database somewhere the moment it upgrades."""
    assert lc.config.get("backupchat_id") in (None, "")
