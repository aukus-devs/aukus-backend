from src.api.event_data.models import (
    PlayerMoveItem,
    SkinItem,
    UnlockedAchievementItem,
)
from src.api.utils import ApiModel
from src.enums import GameDifficulty, GameLength, PlayerKickResult, PlayerMoveType


class PlayerStatsItem(ApiModel):
    player_slug: str
    map_position: int
    total_moves: int
    games_completed: int
    games_dropped: int
    sheikh_moments: int
    rerolls: int
    movies: int
    ladders: int
    snakes: int
    games_0_4: int
    games_5_10: int
    games_11_16: int
    games_17_24: int
    games_25_40: int
    games_40_plus: int
    average_dice_roll: float
    average_move: float
    ladders_moves_sum: int
    snakes_moves_sum: int
    first_achievements: int
    regular_achievements: int
    games_time: int


class PlayerStatsResponse(ApiModel):
    players: list[PlayerStatsItem]


class CreatePlayerMoveRequest(ApiModel):
    type: PlayerMoveType
    item_title: str
    item_length: GameLength | None
    item_review: str
    item_rating: float | None
    game_id: int | None
    cover_image_url: str | None
    difficulty: GameDifficulty | None


class CreatePlayerMoveResponse(ApiModel):
    move_id: int


class FinishPlayerMoveRequest(ApiModel):
    dice_roll_id: int


class FinishPlayerMoveResponse(ApiModel):
    move_to: int
    snake_to: int | None
    ladder_to: int | None
    unlocked_achievements: list[UnlockedAchievementItem]


class DiceRollResult(ApiModel):
    id: int
    roll_values: list[int]


class PlayerMovesQuery(ApiModel):
    players: list[str] = []
    start_ts: int | None = None
    search_title: str | None = None
    titles: list[str] = []
    exclude_ids: list[int] = []


class PlayerMovesResponse(ApiModel):
    moves: list[PlayerMoveItem]
    next_ts: int | None


class PlayerChangeSkinRequest(ApiModel):
    skin_ids: list[int]


class KickResponse(ApiModel):
    result_type: PlayerKickResult


class KickRequest(ApiModel):
    target_player_slug: str


class AddShitRequest(ApiModel):
    amount: int


class UnlockableSkinsResponse(ApiModel):
    skins: list[SkinItem]


class UnlockSkinRequest(ApiModel):
    skin_id: int


class UpdatePlayerMoveRequest(ApiModel):
    item_review: str | None = None
    item_rating: float | None = None
    vod_links: str | None = None
