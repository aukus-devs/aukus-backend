import json
import logging

from sqlalchemy import and_, func, or_, select  # pyright: ignore[reportUnknownVariableType]
from src.api.player.utils import (
    check_achievements_completion,
    get_dice_roll_from_eventlab,
)
from src.db.queries.player_moves import (
    get_players_stats,
    get_all_players,
)
from src.api.player.models import (
    CreatePlayerMoveRequest,
    CreatePlayerMoveResponse,
    FinishPlayerMoveRequest,
    FinishPlayerMoveResponse,
    PlayerChangeSkinRequest,
    PlayerMoveItem,
    PlayerMovesQuery,
    PlayerMovesResponse,
    PlayerStatsItem,
    PlayerStatsResponse,
)
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.consts import MAP_LADDERS, MAP_SNAKES
from src.db.db_models import (
    Player,
    PlayerMove,
    PlayerSkin,
)
from src.db.db_session import get_db
from src.db.queries.player_moves import get_players_latest_moves
from src.enums import GameDifficulty, GameLength, PlayerMoveType
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
    all_players = await get_all_players(db)
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

    cell_from = current_map_position
    cell_to = current_map_position
    if current_map_position == 101 and request.type == PlayerMoveType.COMPLETED:
        cell_to = 102

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
        difficulty_level=request.difficulty.value
        if request.difficulty
        else GameDifficulty.NORMAL.value,
        dice_roll_id=None,
        dice_roll_sum=None,
        dice_roll=None,
        cell_from=cell_from,
        cell_to=cell_to,
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
    direction = (
        -1
        if last_move.type
        in [PlayerMoveType.DROP.value, PlayerMoveType.SHEIKH_MOMENT.value]
        else 1
    )

    next_position = current_map_position + dice_roll_sum * direction
    if next_position < 0:
        next_position = 0
    elif next_position > 101:
        next_position = 101

    position_before_snake_or_ladder = next_position

    ladder_from = None
    ladder_to = None
    snake_from = None
    snake_to = None

    can_use_ladders = last_move.item_length != GameLength.T_0_3.value

    if can_use_ladders and next_position in MAP_LADDERS:
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

    await db.commit()
    unlocked_achievements = await check_achievements_completion(db, current_user)
    unlocked_ids = [a.achievement_id for a in unlocked_achievements]

    return FinishPlayerMoveResponse(
        move_to=position_before_snake_or_ladder,
        snake_to=snake_to,
        ladder_to=ladder_to,
        unlocked_achievements=unlocked_ids,
    )


@router.get("/api/players/moves", response_model=PlayerMovesResponse)
async def get_player_moves(
    params: Annotated[PlayerMovesQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query = select(PlayerMove)
    if params.players:
        query = query.where(PlayerMove.player_slug.in_(params.players))
    if params.start_ts:
        query = query.where(PlayerMove.created_at <= params.start_ts)
    if params.search_title and len(params.search_title) >= 3:
        query = query.where(PlayerMove.item_title.ilike(f"%{params.search_title}%"))
    if params.titles:
        query = query.where(PlayerMove.item_title.in_(params.titles))
    if params.exclude_ids:
        query = query.where(~PlayerMove.id.in_(params.exclude_ids))

    limit = 100

    query = query.order_by(PlayerMove.created_at.desc())
    query = query.limit(limit + 1)

    result = await db.execute(query)
    moves: list[PlayerMove] = result.scalars().all()

    next_item = None
    if len(moves) > limit:
        next_item = moves.pop()

    return PlayerMovesResponse(
        moves=[PlayerMoveItem.model_validate(m) for m in moves],
        next_ts=next_item.created_at if next_item else None,
    )


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
