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
    SHIT_KICK = "shit_kick"


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
    T_0_4 = "0-4"
    T_5_10 = "5-10"
    T_11_16 = "11-16"
    T_17_24 = "17-24"
    T_25_40 = "25-40"
    T_40_PLUS = "40+"


class GameDifficulty(Enum):
    EASY = -1
    NORMAL = 0
    HARD = 1
    VERY_HARD = 2


class DiceOption(Enum):
    D_1D2 = "1d2"
    D_1D4 = "1d4"
    D_2D4 = "2d4"
    D_3D4 = "3d4"
    D_1D6 = "1d6"
    D_2D6 = "2d6"
    D_3D6 = "3d6"
    D_4D6 = "4d6"


class AchievementVisibility(Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class DonationType(Enum):
    SMALL = "small"
    BIG = "big"


class PlayerKickResult(Enum):
    SHIELD_REMOVED = "shield_removed"
    WIN = "win"
    OUT_OF_SHIT = "out_of_shit"
