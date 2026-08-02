# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Test configuration.

``leistungsbot.leistungs_config`` reads its configuration once, at import
time.  The environment therefore has to be populated *before* anything from
``leistungsbot`` is imported - which is why this happens at module level here
and not inside a fixture.

The chat ids and the bot token are forced to fixed test values: the tests
assert on them, so a developer's real configuration must not leak in.

Two things are deliberately *not* forced, because the tests that use them
talk to the real service and would break if we overwrote the credentials:

* the google api key, used by ``google_place_test.py``
* the mysql credentials, used by ``leistungs_db_integration_test.py``

Both fall back to a placeholder when nothing is configured, and the tests
that need them skip when they cannot connect.
"""
from __future__ import annotations

import os

import confuse

TEST_ENV = {
    "LEISTUNGSBOT_BOT_TOKEN": "123456:TEST-TOKEN",
    "LEISTUNGSBOT_API_HASH": "test-api-hash",
    "LEISTUNGSBOT_API_ID": "4711",
    "LEISTUNGSBOT_CHAT_ID": "-1001",
    "LEISTUNGSBOT_LEISTUNGSCHAT_ID": "-1002",
    "LEISTUNGSBOT_LEISTUNGSADMIN_ID": "-1003",
    "LEISTUNGSBOT_USERNAMES": "eckphi",
}

# Only used when nothing real is configured - the integration test skips
# rather than failing when it cannot reach a database.
MYSQL_FALLBACK_ENV = {
    "LEISTUNGSBOT_MYSQL__HOST": "127.0.0.1",
    "LEISTUNGSBOT_MYSQL__DB": "leistungs_db",
    "LEISTUNGSBOT_MYSQL__USER": "leistungs_user",
    "LEISTUNGSBOT_MYSQL__PASSWORD": "test-password",
}


def _google_key_is_configured() -> bool:
    """Whether a google api key can be resolved without our test defaults."""
    probe = confuse.Configuration("LeistungsBot", read=True)
    config_file = os.environ.get("LEISTUNGSBOT_CONFIG_FILE")
    if config_file:
        probe.set_file(config_file, base_for_paths=True)
    probe.set_env()
    return probe["google"].exists()


# googlemaps refuses keys that do not look like one, so keep the prefix.
PLACEHOLDER_GOOGLE_KEY = "AIzaPLACEHOLDER-no-google-api-key-configured"

os.environ.update(TEST_ENV)
for _key, _value in MYSQL_FALLBACK_ENV.items():
    os.environ.setdefault(_key, _value)
if not _google_key_is_configured():
    os.environ["LEISTUNGSBOT_GOOGLE"] = PLACEHOLDER_GOOGLE_KEY

pytest_plugins = ["tests.fixtures"]
