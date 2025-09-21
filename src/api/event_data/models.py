from src.api.utils import ApiModel
from src.enums import SkinSlot


class UnlockedAchievementItem(ApiModel):
    id: int
    unlocked_at: int


class PlayerItem(ApiModel):
    slug: str
    map_position: int
    equipped_skins: list[int]
    unlocked_achievements: list[UnlockedAchievementItem]


class SkinItem(ApiModel):
    id: int
    slot: SkinSlot
    image: str


class AchievementItem(ApiModel):
    id: int
    description: str
    skin_reward_id: int


class EventDataResponse(ApiModel):
    players: list[PlayerItem]
    event_settings: dict[str, str | int | None]
    skins: list[SkinItem]
    achievements: list[AchievementItem]
