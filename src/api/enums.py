from enum import Enum


class Role(Enum):
    PLAYER = "player"
    MODER = "moder"
    ADMIN = "admin"


class StreamPlatform(Enum):
    TWITCH = "twitch"
    VK = "vk"
    KICK = "kick"
    NONE = "none"
