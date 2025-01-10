from __future__ import annotations

from enum import auto
from enum import IntEnum


class ConversationState(IntEnum):
    HISTORY_SELECT_KIND = auto()
    MESSAGE = auto()
    LEISTUNGSPOLL_SELECT_LOCATION = auto()
    LEISTUNGSPOLL_PRESELECT_DATE = auto()
    LEISTUNGSPOLL_SELECT_DATE = auto()
    LEISTUNGSPOLL_PREVIEW = auto()
