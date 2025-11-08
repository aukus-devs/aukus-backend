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
    RULES_EDIT = "rules.edit"


class RulesCategory(Enum):
    GENERAL = "general"
    GAMEPLAY = "gameplay"
    DONATIONS = "donations"


class SkinSlot(Enum):
    HEAD = "head"
    BODY = "body"
    ITEM = "item"
    DICE = "dice"


class GameLength(Enum):
    T_0_3 = "0-3"
    T_3_15 = "3-15"
    T_15_30 = "15-30"
    T_30_plus = "30+"


class GameDifficulty(Enum):
    EASY = -1
    NORMAL = 0
    HARD = 1
    VERY_HARD = 2


class DiceOption(Enum):
    D_1D4 = "1d4"
    D_1D6 = "1d6"
    D_2D6 = "2d6"
    D_3D6 = "3d6"


class AchievementVisibility(Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class DonationType(Enum):
    SMALL = "small"
    BIG = "big"
