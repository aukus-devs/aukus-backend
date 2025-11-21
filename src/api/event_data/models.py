from src.api.player.models import PlayerMoveItem
from src.api.utils import ApiModel
from src.enums import AchievementVisibility, DiceOption, DonationType, SkinSlot


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
    shield_stacks: int
    shit_stacks: int
    skin_rolls: int


class SkinItem(ApiModel):
    id: int
    slot: SkinSlot
    image_url: str


class AchievementItem(ApiModel):
    id: int
    description: str
    reward_skin_id: int
    visibility: AchievementVisibility


class ChatMessageItem(ApiModel):
    id: int
    text: str
    created_at: int


class EventDataResponse(ApiModel):
    players: list[PlayerItem]
    event_settings: dict[str, str | int | None]
    skins: list[SkinItem]
    achievements: list[AchievementItem]
    dice_options: list[DiceOption]
    chat_messages: list[ChatMessageItem]


class DonationItem(ApiModel):
    id: int
    name: str
    type: DonationType
    message: str | None
    created_at: int


class DonationsResponse(ApiModel):
    donations: list[DonationItem]
