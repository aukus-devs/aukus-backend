from enum import Enum


class EventSetting(Enum):
    EVENT_START_TIME = "event_start_time"
    EVENT_END_TIME = "event_end_time"
    ENDPOINT_RESET_DB_ENABLED = "endpoint_reset_db_enabled"


class PlayerMoveType(Enum):
    COMPLETED = "completed"
    REROLL = "reroll"
    DROP = "drop"
    MOVIE = "movie"
    SHEIKH_MOMENT = "sheikh_moment"


class UserRole(Enum):
    ADMIN = "admin"
    STREAMER = "streamer"


class RulesCategory(Enum):
    GENERAL = "general"
    GAMEPLAY = "gameplay"
    DONATIONS = "donations"


class SkinSlot(Enum):
    HEAD = "head"
    BODY = "body"
    SIDE = "side"


class GameLength(Enum):
    T1 = "0-3"
    T2 = "3-5"
    T3 = "5-10"
    T4 = "10-20"
    T5 = "20-25"
    T6 = "25+"


class GameDifficulty(Enum):
    EASY = -1
    NORMAL = 0
    HARD = 1
    VERY_HARD = 2
