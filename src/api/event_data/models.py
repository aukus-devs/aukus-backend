from src.api.player.models import PlayerMoveItem
from src.api.utils import ApiModel
from src.enums import AchievementVisibility, DiceOption, SkinSlot


class UnlockedAchievementItem(ApiModel):
    id: int
    unlocked_at: int


class PlayerItem(ApiModel):
    slug: str
    map_position: int
    equipped_skins: list[int]
    available_skins: list[int]
    unlocked_achievements: list[UnlockedAchievementItem]
    color: str
    last_move: PlayerMoveItem | None


class SkinItem(ApiModel):
    id: int
    slot: SkinSlot
    image_url: str


class AchievementItem(ApiModel):
    id: int
    description: str
    reward_skin_id: int
    visibility: AchievementVisibility


class EventDataResponse(ApiModel):
    players: list[PlayerItem]
    event_settings: dict[str, str | int | None]
    skins: list[SkinItem]
    achievements: list[AchievementItem]
    dice_options: list[DiceOption]
