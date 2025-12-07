import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, or_, select  # pyright: ignore[reportUnknownVariableType]
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.event_data.models import PlayerMoveItem, UnlockedAchievementItem
from src.api.player.models import (
    AddShitRequest,
    CreatePlayerMoveRequest,
    CreatePlayerMoveResponse,
    FinishPlayerMoveRequest,
    FinishPlayerMoveResponse,
    KickRequest,
    KickResponse,
    PlayerChangeSkinRequest,
    PlayerMovesQuery,
    PlayerMovesResponse,
    PlayerStatsItem,
    PlayerStatsResponse,
    UnlockableSkinsResponse,
    UnlockSkinRequest,
    UpdatePlayerMoveRequest,
)
from src.api.player.utils import (
    check_achievements_completion,
    fetch_stream_category_duration,
    get_dice_roll_from_eventlab,
    send_player_move_notification,
)
from src.consts import MAP_LADDERS, MAP_SNAKES
from src.db.db_models import Achievement, Player, PlayerMove, PlayerSkin, Skin
from src.db.db_session import get_db
from src.db.queries.player_moves import (
    get_all_players,
    get_players_by_slugs,
    get_players_latest_moves,
    get_players_stats,
    inc_shield,
    inc_shit,
    process_kick_logic,
)
from src.db.queries.shit_kick import create_kick_shit_event
from src.enums import GameDifficulty, GameLength, PlayerMoveType, UserRole
from src.utils.auth import get_current_player, get_token_payload, security

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
                    games_0_4=0,
                    games_5_10=0,
                    games_11_16=0,
                    games_17_24=0,
                    games_25_40=0,
                    games_40_plus=0,
                    average_dice_roll=0.0,
                    average_move=0.0,
                    ladders_moves_sum=0,
                    snakes_moves_sum=0,
                    first_achievements=0,
                    regular_achievements=0,
                    games_time=0,
                    average_rating=0,
                    shits_thrown=0,
                    shields_used=0,
                )
            )

    return PlayerStatsResponse(players=players)


@router.post("/api/players/move", response_model=CreatePlayerMoveResponse)
async def create_player_move(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: CreatePlayerMoveRequest,
    current_user: Annotated[Player, Depends(get_current_player)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    last_moves = await get_players_latest_moves(db, slugs=[current_user.slug])
    last_move = last_moves.get(current_user.slug)
    current_map_position = last_move.cell_to if last_move else 0

    cell_from = current_map_position
    cell_to = current_map_position
    if current_map_position == 101 and request.type == PlayerMoveType.COMPLETED:
        cell_to = 102

    item_duration = 0
    try:
        item_duration = await fetch_stream_category_duration(
            credentials.credentials, current_user, request.item_title
        )
    except Exception as e:
        logging.warning(f"Failed to get/close stream duration: {e}")

    move = PlayerMove(
        player_slug=current_user.slug,
        type=request.type.value,
        item_title=request.item_title,
        item_review=request.item_review,
        item_rating=request.item_rating,
        item_length=request.item_length.value if request.item_length else None,
        item_duration=item_duration,
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

    if request.type == PlayerMoveType.REROLL:
        async def send_notification_background():
            try:
                _ = await send_player_move_notification(
                    token=credentials.credentials,
                    username=current_user.slug,
                    slug=current_user.slug,
                    move=move,
                )
            except Exception as e:
                logging.warning(f"Failed to send move notification: {e}")

        _ = asyncio.create_task(send_notification_background())

    return CreatePlayerMoveResponse(move_id=move.id)


@router.post("/api/players/move/finish", response_model=FinishPlayerMoveResponse)
async def finish_player_move(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: FinishPlayerMoveRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
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
    elif (
        current_map_position < 81
        and next_position > 81
        and last_move.type == PlayerMoveType.COMPLETED.value
    ):
        normal_steps = 81 - current_map_position
        extra_steps = int((dice_roll_sum - normal_steps) / 2)
        next_position = current_map_position + normal_steps + extra_steps

    position_before_snake_or_ladder = next_position

    ladder_from = None
    ladder_to = None
    snake_from = None
    snake_to = None

    can_use_ladders = True
    # can_use_ladders = last_move.item_length != GameLength.T_0_3.value

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

    if last_move.type == PlayerMoveType.COMPLETED.value:
        match last_move.item_length:
            case GameLength.T_0_4.value:
                current_user.skin_rolls += 1
            case GameLength.T_5_10.value:
                current_user.skin_rolls += 1
            case GameLength.T_11_16.value:
                current_user.skin_rolls += 2
            case GameLength.T_17_24.value:
                current_user.skin_rolls += 2
            case GameLength.T_25_40.value:
                current_user.skin_rolls += 3
            case GameLength.T_40_PLUS.value:
                current_user.skin_rolls += 3
            case _:
                pass

    # commit so that achievements checker gets latest info
    await db.commit()

    unlocked_achievements = await check_achievements_completion(db, current_user)
    await db.flush()

    unlocked_items = [
        UnlockedAchievementItem(
            id=a.achievement_id, unlocked_at=a.created_at, is_first=bool(a.is_first)
        )
        for a in unlocked_achievements
    ]

    async def send_notification_background():
        try:
            _ = await send_player_move_notification(
                token=credentials.credentials,
                username=current_user.slug,
                slug=current_user.slug,
                move=last_move,
            )
        except Exception as e:
            logging.warning(f"Failed to send move notification: {e}")

    _ = asyncio.create_task(send_notification_background())

    return FinishPlayerMoveResponse(
        move_to=position_before_snake_or_ladder,
        snake_to=snake_to,
        ladder_to=ladder_to,
        unlocked_achievements=unlocked_items,
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
        query = query.where(PlayerMove.id.not_in(params.exclude_ids))

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


@router.post("/api/players/kick", response_model=KickResponse)
async def kick_player(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: KickRequest,
):
    slug_map = await get_players_by_slugs(
        db, current_user.slug, request.target_player_slug
    )
    if current_user.slug not in slug_map or request.target_player_slug not in slug_map:
        raise HTTPException(status_code=404, detail="Player not found")

    target = slug_map[request.target_player_slug]

    # current_user = await db.scalar(select(Player).where(Player.slug == "Aboba"))
    # if not current_user:
    #     raise HTTPException(status_code=404, detail="Player 'Aboba' not found")
    #
    # target = await db.scalar(select(Player).where(Player.slug == request.target_player_slug))
    # if not target:
    #     raise HTTPException(status_code=404, detail="Target player not found")

    try:
        result_type = await process_kick_logic(
            kicker=current_user,
            target=target,
        )
        await create_kick_shit_event(
            db,
            player_slug=current_user.slug,
            target_slug=target.slug,
            result=result_type.value,
        )
        await db.flush()
        await db.commit()
        return KickResponse(result_type=result_type)

    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Kick failed")


@router.post("/api/players/add-shit", status_code=200)
async def add_shit(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: AddShitRequest,
):
    amount = request.amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    inc_shit(current_user, amount)
    await create_kick_shit_event(db, player_slug=current_user.slug, result="shit_added")
    await db.flush()
    await db.commit()
    return HTTPException(status_code=200)


@router.post("/api/players/make-shield", status_code=200)
async def make_shield(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
):
    if (current_user.shit_stacks or 0) < 10:
        raise HTTPException(status_code=400, detail="Not enough shit stacks (need 10)")
    if (current_user.shield_stacks or 0) >= 9:
        raise HTTPException(status_code=400, detail="Can not make more than 9 shields")
    if (current_user.shield_stacks or 0) > 6:
        inc_shit(current_user, -10)
        inc_shield(current_user, (9 - current_user.shield_stacks))
    else:
        inc_shit(current_user, -10)
        inc_shield(current_user, 3)
    await create_kick_shit_event(
        db, player_slug=current_user.slug, result="shield_added"
    )
    await db.flush()
    await db.commit()
    return HTTPException(status_code=200)


@router.get("/api/players/unlockable-skins", response_model=UnlockableSkinsResponse)
async def get_unlockable_skins(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
):
    unlocked_skins_query = await db.execute(
        select(PlayerSkin.skin_id).where(PlayerSkin.player_slug == current_user.slug)
    )
    unlocked_skins_ids: list[int] = unlocked_skins_query.scalars().all()

    achievements_skins_query = await db.execute(select(Achievement.reward_skin_id))
    achievements_skins_ids: list[int] = achievements_skins_query.scalars().all()

    query = await db.execute(
        select(Skin)
        .where(Skin.id.not_in(unlocked_skins_ids))
        .where(Skin.id.not_in(achievements_skins_ids))
        .order_by(func.random())
    )
    skins: list[Skin] = query.scalars().all()
    return {"skins": skins}


@router.post("/api/players/unlock-skin", status_code=201)
async def unlock_skin(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_player)],
    request: UnlockSkinRequest,
):
    if current_user.skin_rolls <= 0:
        raise HTTPException(status_code=400, detail="Not enough skin rolls")

    skin_query = await db.execute(select(Skin).where(Skin.id == request.skin_id))
    skin: Skin | None = skin_query.scalars().first()
    if not skin:
        raise HTTPException(status_code=400, detail="Skin not found")

    player_skin_query = await db.execute(
        select(PlayerSkin)
        .where(PlayerSkin.player_slug == current_user.slug)
        .where(PlayerSkin.skin_id == skin.id)
    )

    player_skin: PlayerSkin | None = player_skin_query.scalars().first()
    if player_skin:
        raise HTTPException(status_code=400, detail="skin already unlocked")

    current_user.skin_rolls -= 1
    new_skin = PlayerSkin(
        player_slug=current_user.slug,
        skin_id=skin.id,
        is_equipped=0,
    )
    db.add(new_skin)
    return 201


@router.patch("/api/players/moves/{move_id}", status_code=200)
async def update_player_move(
    move_id: int,
    request: UpdatePlayerMoveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    token_payload = get_token_payload(credentials)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    move_query = await db.execute(select(PlayerMove).where(PlayerMove.id == move_id))
    move: PlayerMove | None = move_query.scalars().first()

    if not move:
        raise HTTPException(status_code=404, detail="Move not found")

    if not (
        UserRole.ADMIN in token_payload.roles
        or token_payload.slug == move.player_slug
        or move.player_slug in token_payload.moder_for
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this move",
        )

    if request.item_review is not None:
        move.item_review = request.item_review
    if request.item_rating is not None:
        move.item_rating = request.item_rating
    if request.vod_links is not None:
        move.vod_links = request.vod_links

    await db.flush()
    await db.commit()

    return {"success": True}
