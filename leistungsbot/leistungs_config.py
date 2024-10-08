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
    "api_id": int,
    "chat_id": int,
    "leistungschat_id": int,
    "leistungsadmin_id": int,
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
config = __config.get(template)  # NOQA


def set_args(namespace: argparse.Namespace, dots: bool = False):
    if namespace.config:
        __config.set_file(
            namespace.config,
            base_for_paths=True,
        )
    __config.set_args(namespace, dots)
    config = __config.get(template)  # NOQA


def __getitem__(self, key):
    return config.get(key)


if __name__ == "__main__":
    assert config["mysql"]["user"] == "leistungs_user"
