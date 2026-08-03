from __future__ import annotations

import argparse
import os

import confuse
import platformdirs

template = {
    "sqlite": {
        "path": confuse.Optional(
            str,
            default=str(
                platformdirs.user_data_path("LeistungsBot")
                / "leistungs_db.sqlite",
            ),
        ),
    },
    "google": str,
    "bot_token": str,
    "api_hash": str,
    "api_id": [int, str],
    "chat_id": [int, str],
    "leistungschat_id": [int, str],
    "leistungsadmin_id": [int, str],
    "backupchat_id": confuse.Optional([int, str]),
    "usernames": confuse.StrSeq(),
    # Absent means no calendar is kept, which is what every deployment did
    # before there was one. See leistungsbot.leistungs_calendar.
    "calendar": confuse.Optional(
        {
            "provider": confuse.Optional(str, default="google"),
            "calendar_id": confuse.Optional(str, default=None),
            "credentials": confuse.Optional(str, default=None),
            # no default: an unset zone is answered by TZ, and only then by
            # Europe/Vienna. See leistungs_calendar.default_timezone.
            "timezone": confuse.Optional(str, default=None),
        },
        default=None,
    ),
}

__config = confuse.Configuration("LeistungsBot", __name__)
if os.environ.get("LEISTUNGSBOT_CONFIG_FILE"):
    __config.set_file(
        os.environ.get(
            "LEISTUNGSBOT_CONFIG_FILE",
        ),
        base_for_paths=True,
    )
__config.set_env()
try:
    config = __config.get(template)  # NOQA
except Exception:
    print(
        "Configuration error: "
        "Please make sure to set the environment variables or provide a configuration file.",
    )
    config = None


def set_args(namespace: argparse.Namespace, dots: bool = False):
    if namespace.config:
        __config.set_file(
            namespace.config,
            base_for_paths=True,
        )
    __config.set_args(namespace, dots)
    global config
    config = __config.get(template)  # NOQA


def __getitem__(self, key):
    return config.get(key)


if __name__ == "__main__":
    print(config["sqlite"]["path"])
