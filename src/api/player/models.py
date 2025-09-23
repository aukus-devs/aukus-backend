from src.api.utils import ApiModel
from src.enums import GameDifficulty, GameLength, PlayerMoveType


class PlayerMoveRequest(ApiModel):
    type: PlayerMoveType
    item_title: str
    item_length: GameLength | None
    item_review: str
    item_rating: float | None
    game_id: int | None
    difficulty: GameDifficulty | None
    dice_roll_id: int | None


class PlayerMoveResponse(ApiModel):
    move_id: int
