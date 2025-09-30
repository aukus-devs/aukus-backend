import json
import logging

from sqlalchemy import or_, select
from src.api.player.utils import get_dice_roll_from_eventlab
from src.db.queries.player_moves import (
    get_players_stats as get_players_stats,
    get_all_players as q_get_all_players,
)
from src.api.player.models import (
    CreatePlayerMoveRequest,
    CreatePlayerMoveResponse,
    FinishPlayerMoveRequest,
    FinishPlayerMoveResponse,
    PlayerChangeSkinRequest,
    PlayerMovesResponse,
    PlayerStatsItem,
    PlayerStatsResponse,
)
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.consts import MAP_LADDERS, MAP_SNAKES
from src.db.db_models import (
    Player,
    PlayerMove,
    PlayerSkin,
)
from src.db.db_session import get_db
from src.db.queries.player_moves import get_players_latest_moves
from src.utils.auth import get_current_player


router = APIRouter(tags=["players"])


@router.get("/api/players/stats", response_model=PlayerStatsResponse)
async def player_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stats = await get_players_stats(db)

    players: list[PlayerStatsItem] = []

    for s in stats:
        average_dice_roll = 0.0
        if s.get("average_dice_roll"):
            average_dice_roll = round(float(s["average_dice_roll"]), 2)

        average_move = 0.0
        if s.get("average_move"):
            average_move = round(float(s["average_move"]), 2)

        players.append(
            PlayerStatsItem.model_validate(
                {
                    **s,
                    "average_dice_roll": average_dice_roll,
                    "average_move": average_move,
                }
            )
        )

    present = {s.player_slug for s in players}
    all_players = await q_get_all_players(db)
    for p in all_players:
        if p.slug not in present:
            players.append(
                PlayerStatsItem(
                    player_slug=p.slug,
                    map_position=0,
                    total_moves=0,
                    games_completed=0,
                    games_dropped=0,
                    sheikh_moments=0,
                    rerolls=0,
                    movies=0,
                    ladders=0,
                    snakes=0,
                    tiny_games=0,
                    short_games=0,
                    medium_games=0,
                    long_games=0,
                    average_dice_roll=0.0,
                    average_move=0.0,
                    ladders_moves_sum=0,
                    snakes_moves_sum=0,
                )
            )

    return PlayerStatsResponse(players=players)


@router.post("/api/players/move", response_model=CreatePlayerMoveResponse)
async def create_player_move(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: CreatePlayerMoveRequest,
    current_user: Annotated[Player, Depends(get_current_player)],
):
    last_moves = await get_players_latest_moves(db, slugs=[current_user.slug])
    last_move = last_moves.get(current_user.slug)
    current_map_position = last_move.cell_to if last_move else 0

    move = PlayerMove(
        player_slug=current_user.slug,
        type=request.type.value,
        item_title=request.item_title,
        item_review=request.item_review,
        item_rating=request.item_rating,
        item_length=request.item_length.value if request.item_length else None,
        item_duration=0,
        game_id=request.game_id,
        cover_image_url=request.cover_image_url,
        difficulty_level=request.difficulty.value if request.difficulty else None,
        dice_roll_id=None,
        dice_roll_sum=None,
        dice_roll=None,
        cell_from=current_map_position,
        cell_to=current_map_position,
        ladder_from=None,
        ladder_to=None,
        snake_from=None,
        snake_to=None,
    )

    db.add(move)
    await db.flush()

    return CreatePlayerMoveResponse(move_id=move.id)


@router.post("/api/players/move/finish", response_model=FinishPlayerMoveResponse)
async def finish_player_move(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: FinishPlayerMoveRequest,
):
    last_moves = await get_players_latest_moves(db, slugs=[current_user.slug])
    last_move = last_moves.get(current_user.slug)

    if not last_move:
        raise HTTPException(status_code=400, detail="No active move found")

    current_map_position = last_move.cell_from

    try:
        dice_roll = await get_dice_roll_from_eventlab(request.dice_roll_id)
    except Exception:
        logging.exception("Failed to fetch dice roll")
        raise HTTPException(status_code=400, detail="Failed to fetch dice roll")

    dice_roll_sum = sum(dice_roll.roll_values)
    next_position = current_map_position + dice_roll_sum
    position_before_snake_or_ladder = next_position

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

    last_move.cell_to = next_position
    last_move.ladder_from = ladder_from
    last_move.ladder_to = ladder_to
    last_move.snake_from = snake_from
    last_move.snake_to = snake_to

    last_move.dice_roll_id = request.dice_roll_id
    last_move.dice_roll_sum = dice_roll_sum
    last_move.dice_roll = json.dumps(dice_roll.roll_values)

    return FinishPlayerMoveResponse(
        move_to=position_before_snake_or_ladder, snake_to=snake_to, ladder_to=ladder_to
    )


@router.get("/api/players/{player_slug}/moves", response_model=PlayerMovesResponse)
async def get_player_moves(
    player_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(PlayerMove)
        .where(PlayerMove.player_slug == player_slug)
        .order_by(PlayerMove.created_at.desc())
    )
    moves = result.scalars().all()
    return PlayerMovesResponse(moves=moves)


@router.post("/api/players/skins")
async def set_player_skins(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: PlayerChangeSkinRequest,
):
    player_skins_query = select(PlayerSkin).where(
        PlayerSkin.player_slug == current_user.slug,
        or_(
            PlayerSkin.skin_id.in_(request.skin_ids),
            PlayerSkin.is_equipped == 1,
        ),
    )
    result = await db.execute(player_skins_query)
    player_skins: list[PlayerSkin] = result.scalars().all()
    player_skins_by_id = {skin.skin_id: skin for skin in player_skins}

    for skin in player_skins:
        skin.is_equipped = 0

    for skin_id in request.skin_ids:
        player_skin = player_skins_by_id.get(skin_id)
        if player_skin:
            player_skin.is_equipped = 1

    return HTTPException(status_code=200)
