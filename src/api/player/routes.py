from src.db.queries.player_moves import get_players_stats as q_get_players_stats, get_all_players as q_get_all_players
from src.api.player.models import PlayerStatsItem, PlayerStatsResponse
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

router = APIRouter(tags=["players"])


@router.get("/api/player_stats", response_model=PlayerStatsResponse)
async def player_stats(
        # current_player: Annotated[Player, Depends(get_current_player)],
        db: Annotated[AsyncSession, Depends(get_db)],
):
    stats = await q_get_players_stats(db)

    players: list[PlayerStatsItem] = [
        PlayerStatsItem(
            player_slug=s["player_slug"],
            map_position=int(s["map_position"]),
            total_moves=int(s["total_moves"]),
            games_completed=int(s["games_completed"]),
            games_dropped=int(s["games_dropped"]),
            sheikh_moments=int(s["sheikh_moments"]),
            rerolls=int(s["rerolls"]),
            movies=int(s["movies"]),
            ladders=int(s["ladders"]),
            snakes=int(s["snakes"]),
            tiny_games=int(s["tiny_games"]),
            short_games=int(s["short_games"]),
            medium_games=int(s["medium_games"]),
            long_games=int(s["long_games"]),
            average_dice_roll=round(float(s["average_dice_roll"]), 2) if s["average_dice_roll"] is not None else 0.0,
            average_move=round(float(s["average_move"]), 2) if s["average_move"] is not None else 0.0,
            ladders_moves_sum=int(s["ladders_moves_sum"]),
            snakes_moves_sum=int(s["snakes_moves_sum"]),
        )
        for s in stats
    ]

    present = {s.player_slug for s in players}
    all_players = await q_get_all_players(db)
    for p in all_players:
        slug = p["player_slug"]
        if slug not in present:
            players.append(
                PlayerStatsItem(
                    player_slug=slug,
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
