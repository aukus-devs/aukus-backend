import json
from typing import Any

from pydantic import field_validator

from src.api.utils import ApiModel
from src.enums import (
    AchievementVisibility,
    DiceOption,
    DonationType,
    GameDifficulty,
    GameLength,
    PlayerMoveType,
    SkinSlot,
)


class PlayerMoveItem(ApiModel):
    id: int
    created_at: int
    updated_at: int
    player_slug: str
    type: PlayerMoveType
    item_title: str
    item_duration: int
    item_review: str
    item_rating: float
    item_length: GameLength | None
    vod_links: str | None
    game_id: int | None
    cover_image_url: str | None
    difficulty_level: GameDifficulty
    cell_from: int
    cell_to: int
    ladder_from: int | None
    ladder_to: int | None
    snake_from: int | None
    snake_to: int | None
    dice_roll_id: int | None
    dice_roll_sum: int | None
    dice_roll: list[int] | None

    @field_validator("dice_roll", mode="before")
    @classmethod
    def parse_dice_roll(cls, v: Any) -> Any:  # pyright: ignore[reportAny, reportExplicitAny]
        if isinstance(v, str):
            try:
                return json.loads(v)  # pyright: ignore[reportAny]
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON format for dice_roll: {v}")
        return v  # pyright: ignore[reportAny]


class UnlockedAchievementItem(ApiModel):
    id: int
    unlocked_at: int
    is_first: bool


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
    points: int


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
