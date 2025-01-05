from __future__ import annotations

import argparse
import os

import confuse

template = {
    "mysql": {
        "host": confuse.Optional(str),
        "db": confuse.Optional(str),
        "user": confuse.Optional(str),
        "password": confuse.Optional(str),
    },
    "google": str,
    "bot_token": str,
    "api_hash": str,
    "api_id": [int, str],
    "chat_id": [int, str],
    "leistungschat_id": [int, str],
    "leistungsadmin_id": [int, str],
    "usernames": confuse.StrSeq(),
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
    assert config["mysql"]["user"] == "leistungs_user"
