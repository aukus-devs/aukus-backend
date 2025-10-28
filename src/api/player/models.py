import json
from typing import Any
from pydantic import field_validator
from src.api.utils import ApiModel
from src.enums import GameDifficulty, GameLength, PlayerMoveType


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
    tiny_games: int
    short_games: int
    medium_games: int
    long_games: int
    average_dice_roll: float
    average_move: float
    ladders_moves_sum: int
    snakes_moves_sum: int


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
    unlocked_achievements: list[int]


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


class DiceRollResult(ApiModel):
    id: int
    roll_values: list[int]


class PlayerMovesQuery(ApiModel):
    player_slug: str | None = None
    start_ts: int | None = None


class PlayerMovesResponse(ApiModel):
    moves: list[PlayerMoveItem]
    other_players: list[PlayerMoveItem]
    next_ts: int | None


class PlayerChangeSkinRequest(ApiModel):
    skin_ids: list[int]
