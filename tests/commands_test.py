# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The command registry, /help, and the menu telegram is told about.

The interesting test here is `test_every_registered_command_is_in_the
_registry`: it reads the commands back off the live TeleBot instance, so a
handler that stops going through `Commands` fails the suite instead of
quietly dropping out of /help.
"""

from __future__ import annotations

from leistungsbot import Commands
from tests import support


def registered_commands(app) -> set[str]:
    """Every command name telebot will actually dispatch on."""
    found: set[str] = set()
    for handler in app.bot.message_handlers:
        found.update(handler["filters"].get("commands") or [])
    return found


def registry_commands() -> set[str]:
    return {name for c in Commands.ALL for name in c.names}


def test_every_registered_command_is_in_the_registry(app):
    assert registered_commands(app) - registry_commands() == set()


def test_every_registry_command_has_a_handler(app):
    assert registry_commands() - registered_commands(app) == set()


def test_command_names_are_unique():
    names = [name for c in Commands.ALL for name in c.names]
    assert len(names) == len(set(names))


def test_no_command_carries_a_leading_slash():
    # /help builds them, telegram rejects them with one
    assert all(not c.command.startswith("/") for c in Commands.ALL)


def test_aliases_reach_the_same_handler(app):
    handlers = [
        h["function"]
        for h in app.bot.message_handlers
        if "stats" in (h["filters"].get("commands") or [])
    ]
    assert len(handlers) == 1
    assert (
        "groups"
        in [
            h["filters"]["commands"]
            for h in app.bot.message_handlers
            if h["function"] is handlers[0]
        ][0]
    )


# --- what each audience is told ----------------------------------------


def test_public_sees_only_public_commands():
    visible = Commands.visible_to(Commands.Access.PUBLIC)
    assert all(c.access is Commands.Access.PUBLIC for c in visible)
    assert Commands.PURGE not in visible
    assert Commands.HELP in visible


def test_admin_sees_the_admin_commands_too():
    visible = Commands.visible_to(Commands.Access.ADMIN)
    assert Commands.PURGE in visible
    assert Commands.HELP in visible
    assert Commands.BOTLOGS not in visible


def test_owner_sees_everything():
    assert Commands.visible_to(Commands.Access.OWNER) == list(Commands.ALL)


# --- /help --------------------------------------------------------------


def test_help_lists_the_commands(app):
    support.send(app, support.make_message("/help"))
    said = "\n".join(support.sent_texts(app))
    assert "/leistungspoll - Create a new poll for next week" in said
    support.assert_no_dev_error(app)


def test_help_keeps_the_joke(app):
    support.send(app, support.make_message("/help"))
    support.assert_said(app, "Eiso i hüf da do ned")


# The sender is an owner by username *and* an admin of the leistungschat by
# default, so the audience tests have to say who is asking. `pleb` demotes
# the chat membership, `username=` steps out of the `usernames` config.
STRANGER = "hackl"


def test_help_hides_admin_commands_from_a_pleb(pleb):
    support.send(pleb, support.make_message("/help", username=STRANGER))
    support.assert_not_said(pleb, "/purge")
    support.assert_not_said(pleb, "/botlogs")
    support.assert_said(pleb, "/alive")


def test_help_shows_admin_commands_to_an_admin(app):
    support.send(app, support.make_message("/help", username=STRANGER))
    support.assert_said(app, "/purge")
    support.assert_not_said(app, "/botlogs")


def test_help_shows_everything_to_an_owner(app):
    support.send(app, support.make_message("/help"))
    support.assert_said(app, "/botlogs")


def test_a_stranger_stays_public_when_telegram_cannot_be_asked(app):
    app.bot.get_chat_member.side_effect = RuntimeError("no such chat")
    message = support.make_message("/help", username=STRANGER)
    assert app.access_of(message) is Commands.Access.PUBLIC


# --- the menu telegram gets --------------------------------------------


def test_publish_commands_sends_only_the_public_ones(app):
    app.publish_commands()

    published = app.bot.set_my_commands.call_args.args[0]
    names = [c.command for c in published]

    assert "help" in names
    assert "purge" not in names
    assert "botlogs" not in names


def test_publish_commands_survives_a_failing_api(app):
    app.bot.set_my_commands.side_effect = RuntimeError("telegram said no")
    app.publish_commands()  # must not raise
