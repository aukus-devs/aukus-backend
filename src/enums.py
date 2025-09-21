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
