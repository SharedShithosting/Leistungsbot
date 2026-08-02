# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Who may press which button. Closes #99.

The message an inline keyboard sits on was sent by the bot, so its author is
the bot's own account. Handing that message to `sender_has_permission` asks
whether the *bot* is an administrator of the leistungschat - and it is, it
has to pin and stop polls, so every admin button said yes to everybody.

The presser is `call.from_user`, and that is what these tests demote. The bot
stays an administrator throughout, exactly as in a real chat: if the check
looks at the wrong one, every test in here fails.
"""

from __future__ import annotations

import pytest

from leistungsbot.handlers.callbacks import ADMIN_CALLBACKS
from leistungsbot.states import LeistungsState
from tests import support

REFUSAL = "nicht für den Pöbel"
OPEN_KEY = 10


def enter(app, state_name: str, user_id: int = support.ADMIN_USER_ID) -> None:
    app.bot.set_state(
        user_id,
        getattr(LeistungsState, state_name),
        support.GROUP_CHAT_ID,
    )


# --- the buttons behind the admin commands ------------------------------


def test_a_pleb_cannot_remind(pleb, db):
    enter(pleb, "remindePoll")

    support.press(pleb, {"🍻open": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    support.assert_not_said(pleb, "Da Reminder is draußen!")


def test_a_pleb_cannot_close_a_poll(pleb, db):
    enter(pleb, "closePoll")

    support.press(pleb, {"🍻open": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    db.closeLeistungstag.assert_not_called()
    pleb.bot.stop_poll.assert_not_called()


def test_a_pleb_cannot_sneaky_close_a_poll(pleb, db):
    enter(pleb, "sneakyClosePoll")

    support.press(pleb, {"🍻open": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    db.closeLeistungstag.assert_not_called()


def test_a_pleb_cannot_send_a_message_to_the_leistungschat(pleb):
    enter(pleb, "genericLeistungsmessage")

    support.press(
        pleb,
        {"🍻open": OPEN_KEY},
        reply_to_message=support.message_payload("/message hallo"),
    )

    support.assert_said(pleb, REFUSAL)
    support.assert_not_said(pleb, "hallo")


def test_a_pleb_cannot_send_a_message_without_a_poll(pleb):
    """The "Nö" button of /message: same message, no poll to reply to."""
    support.press(
        pleb,
        {"🍻no": None},
        reply_to_message=support.message_payload("/message hallo"),
    )

    support.assert_said(pleb, REFUSAL)
    support.assert_not_said(pleb, "hallo")


def test_a_pleb_cannot_pick_a_kind_to_purge(pleb):
    support.press(pleb, {"🍻purge_type": 1})

    support.assert_said(pleb, REFUSAL)
    support.assert_not_said(pleb, "Welchen Leistungstag willst löschen?")


def test_a_pleb_cannot_ask_what_a_purge_would_delete(pleb, db):
    support.press(pleb, {"🍻dry_purge": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    db.getLeistungstag.assert_not_called()


def test_a_pleb_cannot_purge(pleb, db):
    support.press(pleb, {"🍻purge": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    db.removeLeistungstag.assert_not_called()
    pleb.bot.delete_message.assert_not_called()


def test_a_pleb_cannot_publish_a_leistungstag(pleb, db):
    support.press(pleb, {"🍻publish": 12345})

    support.assert_said(pleb, REFUSAL)
    db.addLeistungsTag.assert_not_called()
    pleb.bot.send_poll.assert_not_called()


def test_a_pleb_cannot_confirm_a_closed_poll(pleb):
    support.press(pleb, {"🍻closed": OPEN_KEY})

    support.assert_said(pleb, REFUSAL)
    support.assert_not_said(pleb, "Der Poll is scho closed")


def test_a_pleb_cannot_pick_a_poll_date(pleb):
    support.press(pleb, {"🍻poll_date": "04.08.2026"})

    support.assert_said(pleb, REFUSAL)
    pleb.bot.send_poll.assert_not_called()


def test_a_pleb_cannot_wave_the_open_hours_through(pleb):
    support.press(pleb, {"🍻open_hours_checked": True})

    support.assert_said(pleb, REFUSAL)
    pleb.bot.send_poll.assert_not_called()


def test_the_refusal_leaves_the_keyboard_alone(pleb):
    """An admin has to be able to press the same button afterwards."""
    enter(pleb, "closePoll")

    support.press(pleb, {"🍻open": OPEN_KEY})

    pleb.bot.edit_message_reply_markup.assert_not_called()


# --- the public ones keep working ---------------------------------------


def test_a_pleb_may_still_cancel(pleb):
    enter(pleb, "searchLocation")

    support.press(pleb, {"🍻cancel": None})

    support.assert_not_said(pleb, REFUSAL)
    assert support.state_of(pleb) is None


def test_a_pleb_may_still_read_the_history(pleb):
    support.press(pleb, {"🍻history": OPEN_KEY})

    support.assert_not_said(pleb, REFUSAL)
    support.assert_said(pleb, "Bar A")


def test_a_pleb_may_still_look_at_a_location(pleb):
    support.press(pleb, {"🍻location": 1})

    support.assert_not_said(pleb, REFUSAL)
    support.assert_no_dev_error(pleb)


def test_a_pleb_may_still_pick_a_kind_of_history(pleb):
    support.press(pleb, {"🍻history_type": 1})

    support.assert_not_said(pleb, REFUSAL)
    support.assert_said(pleb, "Welchen Leistungstag willst da anschaun?")


# --- the other half of the bug ------------------------------------------


def test_an_admin_is_let_through_when_the_bot_is_not_an_admin(app, db):
    """The failure mode in a chat where the bot was never promoted.

    Checking `call.message` there refuses everybody, admins included -
    telegram reports the bot as a plain member.
    """
    app.plebs.add(support.BOT_USER_ID)
    enter(app, "closePoll")

    support.press(app, {"🍻open": OPEN_KEY})

    support.assert_not_said(app, REFUSAL)
    db.closeLeistungstag.assert_called_once_with(OPEN_KEY)


def test_the_presser_is_asked_about_and_not_the_carrier(app):
    """Straight at the api call: the id handed to telegram is the presser."""
    other = 4004
    app.plebs.add(other)
    enter(app, "closePoll")

    support.press(app, {"🍻open": OPEN_KEY}, user_id=support.ADMIN_USER_ID)

    asked = [
        args[1] for name, args, _ in app.outbox if name == "get_chat_member"
    ]
    assert asked, "nobody's permission was checked at all"
    assert support.BOT_USER_ID not in asked
    assert asked == [support.ADMIN_USER_ID] * len(asked)


# --- the list itself ----------------------------------------------------


@pytest.mark.parametrize("cmd", sorted(ADMIN_CALLBACKS))
def test_every_admin_callback_refuses_a_pleb(pleb, cmd):
    """Guards the registry: a button added to it has to actually refuse.

    Payload values are nonsense on purpose - the check has to come first.
    """
    support.press(
        pleb,
        {f"🍻{cmd}": OPEN_KEY},
        reply_to_message=support.message_payload("/message hallo"),
    )

    support.assert_said(pleb, REFUSAL)


def test_the_public_callbacks_are_not_in_the_admin_list():
    """The flows anybody may run: adding a location, history, ratings."""
    assert ADMIN_CALLBACKS.isdisjoint(
        {
            "cancel",
            "search",
            "select",
            "q",
            "history",
            "history_type",
            "location",
        },
    )


def test_an_unknown_leistungstag_is_still_reported_to_the_devs(app, db):
    """The gate must not swallow the catch-all for unhandled callbacks."""
    support.press(app, {"🍻nonsense": 1})

    support.assert_said(app, "Handle this callback")
