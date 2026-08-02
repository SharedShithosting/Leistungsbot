# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Test helpers: telegram object factories, dispatch and assertions.

The tests drive the bot the way telegram does - by pushing ``Message`` /
``CallbackQuery`` objects through ``TeleBot.process_new_*``.  Nothing in here
knows the name of a handler function, so handlers may be renamed, moved or
regrouped during a refactor without touching the tests.
"""

from __future__ import annotations

import json
from typing import Any

import telebot

DEV_CHAT_ID = -1001
LEISTUNGSCHAT_ID = -1002
LEISTUNGSADMIN_ID = -1003

ADMIN_USER_ID = 42
ADMIN_USERNAME = "eckphi"
GROUP_CHAT_ID = 100


def message_payload(
    text: str,
    user_id: int = ADMIN_USER_ID,
    chat_id: int = GROUP_CHAT_ID,
    chat_type: str = "group",
    username: str = ADMIN_USERNAME,
    message_id: int = 1,
    reply_to_message: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The raw update dict telegram would send for a text message."""
    payload: dict[str, Any] = {
        "message_id": message_id,
        "from": {
            "id": user_id,
            "is_bot": False,
            "first_name": "Test",
            "username": username,
        },
        "chat": {"id": chat_id, "type": chat_type},
        "date": 1700000000,
        "text": text,
    }
    if reply_to_message is not None:
        payload["reply_to_message"] = reply_to_message
    return payload


def make_message(text: str, **kwargs) -> telebot.types.Message:
    """Build a text message as telegram would deliver it."""
    return telebot.types.Message.de_json(message_payload(text, **kwargs))


def make_callback(
    data: dict[str, Any],
    user_id: int = ADMIN_USER_ID,
    chat_id: int = GROUP_CHAT_ID,
    message_id: int = 1,
    reply_to_message: dict[str, Any] | None = None,
) -> telebot.types.CallbackQuery:
    """Build a callback query carrying the bot's json ``{"🍻cmd": value}``."""
    message = message_payload(
        "poll message",
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        reply_to_message=reply_to_message,
    )
    return telebot.types.CallbackQuery.de_json(
        {
            "id": "cb-1",
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Test",
                "username": ADMIN_USERNAME,
            },
            "chat_instance": "chat-instance",
            "data": json.dumps(data),
            "message": message,
        },
    )


def send(app, message: telebot.types.Message) -> telebot.types.Message:
    """Deliver a message to the bot and return it."""
    app.bot.process_new_messages([message])
    return message


def send_command(app, text: str, **kwargs) -> telebot.types.Message:
    return send(app, make_message(text, **kwargs))


def press(app, data: dict[str, Any], **kwargs) -> telebot.types.CallbackQuery:
    """Deliver an inline button press to the bot and return the query."""
    call = make_callback(data, **kwargs)
    app.bot.process_new_callback_query([call])
    return call


def press_raw(app, data: str, **kwargs) -> telebot.types.CallbackQuery:
    """Like :func:`press`, but for buttons that do not carry the bot's json."""
    call = make_callback({}, **kwargs)
    call.data = data
    app.bot.process_new_callback_query([call])
    return call


def pick_calendar_date(app, target) -> None:
    """Click through the telegram calendar: year, then month, then day."""
    for step, wanted in (
        ("y", target.year),
        ("m", target.month),
        ("d", target.day),
    ):
        data = _calendar_button(last_markup(app), step, wanted)
        assert data, f"no calendar button for {step}={wanted}"
        press_raw(app, data)


def _calendar_button(markup, step: str, wanted: int) -> str | None:
    """``cbcal_<id>_<action>_<step>_<year>_<month>_<day>``, action ``s`` selects."""
    position = {"y": 4, "m": 5, "d": 6}[step]
    for button in _buttons(markup):
        data = button.get("callback_data", "")
        parts = data.split("_")
        if len(parts) < 7 or parts[0] != "cbcal":
            continue
        if (
            parts[2] == "s"
            and parts[3] == step
            and int(parts[position]) == wanted
        ):
            return data
    return None


# ────────────────────────────── assertions ──────────────────────────────


TEXT_METHODS = ("send_message", "reply_to")


def sent_texts(app) -> list[str]:
    """Every text the bot sent, in order, via ``send_message`` or ``reply_to``.

    ``send_animation`` captions are included as well, they carry text too.
    """
    texts = []
    for name, args, kwargs in app.outbox:
        if name in TEXT_METHODS and len(args) > 1:
            texts.append(args[1])
        elif name == "send_animation" and kwargs.get("caption"):
            texts.append(kwargs["caption"])
    return texts


def assert_said(app, snippet: str) -> None:
    texts = sent_texts(app)
    assert any(
        snippet in t for t in texts
    ), f"expected a message containing {snippet!r}, got {texts!r}"


def assert_not_said(app, snippet: str) -> None:
    texts = sent_texts(app)
    assert not any(
        snippet in t for t in texts
    ), f"did not expect a message containing {snippet!r}, got {texts!r}"


def sent_documents(app) -> list[tuple[int, str | None, bytes]]:
    """``(chat_id, visible_file_name, content)`` per document the bot sent."""
    return app.documents


def assert_no_dev_error(app) -> None:
    """Fail on the bot's catch-all error paths.

    Every handler wraps its body in ``except Exception`` and reports to the
    dev chat.  Without this check a broken handler would look like a passing
    test, so call it in every happy-path test.
    """
    errors = [
        t
        for t in sent_texts(app)
        if "Hi Devs" in t or "An error occurred" in t
    ]
    assert not errors, f"handler raised: {errors!r}"


def _buttons(markup) -> list[dict[str, Any]]:
    """Flatten any keyboard into a list of button dicts.

    Handles the three shapes the bot produces: ``InlineKeyboardMarkup``,
    ``ReplyKeyboardMarkup`` and the json string the calendar library builds.
    """
    if isinstance(markup, str):
        data = json.loads(markup)
    elif isinstance(markup, dict):
        data = markup
    else:
        data = json.loads(markup.to_json())

    rows = data.get("inline_keyboard") or data.get("keyboard") or []
    return [
        button if isinstance(button, dict) else button.to_dict()
        for row in rows
        for button in row
    ]


def button_labels(markup) -> list[str]:
    return [b["text"] for b in _buttons(markup)]


def callback_payloads(markup) -> list[dict[str, Any]]:
    """The bot's own ``{"🍻cmd": value}`` payloads; other buttons are ignored."""
    payloads = []
    for button in _buttons(markup):
        data = button.get("callback_data")
        if not data:
            continue
        try:
            payloads.append(json.loads(data))
        except ValueError:
            continue  # e.g. the calendar's "cbcal_..." buttons
    return payloads


def last_markup(app) -> Any:
    """``reply_markup`` of the most recent outgoing message."""
    for _name, _args, kwargs in reversed(app.outbox):
        markup = kwargs.get("reply_markup")
        if markup is not None:
            return markup
    raise AssertionError("no message with a reply_markup was sent")


def state_of(app, user_id: int = ADMIN_USER_ID, chat_id: int = GROUP_CHAT_ID):
    return app.bot.get_state(user_id, chat_id)
