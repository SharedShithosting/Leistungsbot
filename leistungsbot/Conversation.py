
from enum import IntEnum, auto

class ConversationState(IntEnum):
    HISTORY_SELECT_KIND = auto()
    LEISTUNGSPOLL_SELECT_LOCATION = auto()
    LEISTUNGSPOLL_PRESELECT_DATE = auto()
    LEISTUNGSPOLL_SELECT_DATE = auto()
    LEISTUNGSPOLL_PREVIEW = auto()
