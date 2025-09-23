from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from src.api.player.models import PlayerMoveRequest, PlayerMoveResponse
from src.consts import MAP_LADDERS, MAP_SNAKES
from src.db.db_models import (
    Player,
    PlayerMove,
)
from src.db.db_session import get_db
from src.db.queries.player_moves import get_players_latest_moves
from src.utils.auth import get_current_player

router = APIRouter(tags=["player"])


@router.post("/api/player/move", response_model=PlayerMoveResponse)
async def make_player_move(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: PlayerMoveRequest,
    current_user: Annotated[Player, Depends(get_current_player)],
):
    last_moves = await get_players_latest_moves(db, slugs=[current_user.slug])
    last_move = last_moves.get(current_user.slug)
    current_map_position = last_move.cell_to if last_move else 0

    # TODO: get actual dice roll by id
    dice_roll_sum = 5
    next_position = current_map_position + dice_roll_sum

    ladder_from = None
    ladder_to = None
    snake_from = None
    snake_to = None

    if next_position in MAP_LADDERS:
        ladder_from = next_position
        next_position = MAP_LADDERS[next_position]
        ladder_to = next_position

    if next_position in MAP_SNAKES:
        snake_from = next_position
        next_position = MAP_SNAKES[next_position]
        snake_to = next_position

    move = PlayerMove(
        player_slug=current_user.slug,
        type=request.type.value,
        item_title=request.item_title,
        item_review=request.item_review,
        item_rating=request.item_rating,
        item_length=request.item_length.value if request.item_length else None,
        item_duration=0,
        game_id=request.game_id,
        difficulty_level=request.difficulty.value if request.difficulty else None,
        dice_roll_id=request.dice_roll_id,
        cell_from=current_map_position,
        cell_to=next_position,
        ladder_from=ladder_from,
        ladder_to=ladder_to,
        snake_from=snake_from,
        snake_to=snake_to,
    )

    db.add(move)
    await db.flush()
    return {"move_id": move.id}
