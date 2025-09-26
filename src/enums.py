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
    T1 = "0-5"
    T2 = "5-15"
    T3 = "15-30"
    T4 = "30+"


class GameDifficulty(Enum):
    EASY = -1
    NORMAL = 0
    HARD = 1
    VERY_HARD = 2
