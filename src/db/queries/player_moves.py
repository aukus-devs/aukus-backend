from __future__ import annotations

from sqlalchemy import select, func, case, and_, cast, Float  # pyright: ignore[reportUnknownVariableType]
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_models import Player, PlayerMove
from src.enums import GameLength, PlayerMoveType, PlayerKickResult


async def get_players_latest_moves(
        db: AsyncSession, *, slugs: list[str] | None = None
) -> dict[str, PlayerMove]:
    # Base query: optionally filter by slugs first
    base_stmt = select(PlayerMove)
    if slugs:
        base_stmt = base_stmt.where(PlayerMove.player_slug.in_(slugs))

    # Subquery: rank moves per player by id
    stmt = (
        select(
            PlayerMove,
            func.row_number()
            .over(partition_by=PlayerMove.player_slug, order_by=PlayerMove.id.desc())
            .label("rnk"),
        )
        .select_from(base_stmt.subquery())
        .subquery()
    )

    # Select only the latest (row_number = 1)
    query = (
        select(PlayerMove).join(stmt, PlayerMove.id == stmt.c.id).where(stmt.c.rnk == 1)
    )

    result = await db.execute(query)
    moves: list[PlayerMove] = result.scalars().all()
    return {move.player_slug: move for move in moves}


async def get_players_stats(db: AsyncSession) -> list[dict[str, str | int | float]]:
    pm = PlayerMove

    total_moves = func.count().label("total_moves")
    games_completed = func.sum(
        case((pm.type == PlayerMoveType.COMPLETED.value, 1), else_=0)
    ).label("games_completed")
    games_dropped = func.sum(
        case((pm.type == PlayerMoveType.DROP.value, 1), else_=0)
    ).label("games_dropped")
    sheikh_moments = func.sum(
        case((pm.type == PlayerMoveType.SHEIKH_MOMENT.value, 1), else_=0)
    ).label("sheikh_moments")
    rerolls = func.sum(
        case((pm.type == PlayerMoveType.REROLL.value, 1), else_=0)
    ).label("rerolls")
    movies = func.sum(case((pm.type == PlayerMoveType.MOVIE.value, 1), else_=0)).label(
        "movies"
    )
    ladders = func.sum(case((pm.ladder_from.is_not(None), 1), else_=0)).label("ladders")
    snakes = func.sum(case((pm.snake_from.is_not(None), 1), else_=0)).label("snakes")

    tiny_games = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_0_3.value,
            ),
            else_=0,
        )
    ).label("tiny_games")
    short_games = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_3_15.value,
            ),
            else_=0,
        )
    ).label("short_games")
    medium_games = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_15_30.value,
            ),
            else_=0,
        )
    ).label("medium_games")
    long_games = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_30_plus.value,
            ),
            else_=0,
        )
    ).label("long_games")

    dr = cast(pm.dice_roll_sum, Float)
    average_move = func.avg(
        case((pm.type != PlayerMoveType.REROLL.value, func.abs(dr)), else_=None)
    ).label("average_move")

    average_dice_roll = func.avg(
        case(
            (pm.cell_to > 101, None),
            (
                pm.item_length.in_((GameLength.T_0_3.value, GameLength.T_3_15.value)),
                func.abs(dr),
            ),
            (
                and_(pm.item_length == GameLength.T_15_30.value, pm.cell_from < 81),
                func.abs(dr / 2.0),
            ),
            (
                and_(pm.item_length == GameLength.T_30_plus.value, pm.cell_from < 81),
                func.abs(dr / 3.0),
            ),
            (
                and_(
                    pm.cell_from < 81,
                    pm.type.in_(
                        (PlayerMoveType.DROP.value, PlayerMoveType.SHEIKH_MOMENT.value)
                    ),
                ),
                func.abs(dr),
            ),
            (
                and_(
                    pm.cell_from >= 81,
                    pm.item_length.in_(
                        (GameLength.T_15_30.value, GameLength.T_30_plus.value)
                    ),
                ),
                func.abs(dr),
            ),
            (
                and_(
                    pm.cell_from >= 81,
                    pm.type.in_(
                        (PlayerMoveType.DROP.value, PlayerMoveType.SHEIKH_MOMENT.value)
                    ),
                ),
                func.abs(dr / 2.0),
            ),
            else_=None,
        )
    ).label("average_dice_roll")

    ladders_moves_sum = func.sum(
        case(
            (
                and_(pm.ladder_from.is_not(None), pm.ladder_to.is_not(None)),
                pm.ladder_to - pm.ladder_from,
            ),
            else_=0,
        )
    ).label("ladders_moves_sum")

    snakes_moves_sum = func.sum(
        case(
            (
                and_(pm.snake_from.is_not(None), pm.snake_to.is_not(None)),
                pm.snake_to - pm.snake_from,
            ),
            else_=0,
        )
    ).label("snakes_moves_sum")

    last_moves = await get_players_latest_moves(db)
    map_pos_by_slug = {slug: move.cell_to for slug, move in last_moves.items()}

    q = (
        select(
            pm.player_slug,
            total_moves,
            games_completed,
            games_dropped,
            sheikh_moments,
            rerolls,
            movies,
            ladders,
            snakes,
            tiny_games,
            short_games,
            medium_games,
            long_games,
            average_move,
            average_dice_roll,
            ladders_moves_sum,
            snakes_moves_sum,
        )
        .select_from(pm)
        .group_by(pm.player_slug)
    )

    res = await db.execute(q)
    rows = res.mappings().all()

    return [
        {
            **dict(r),
            "map_position": int(map_pos_by_slug.get(r["player_slug"], 0)),  # pyright: ignore[reportAny]
        }
        for r in rows
    ]


async def get_all_players(db: AsyncSession) -> list[Player]:
    res = await db.execute(select(Player))
    return res.scalars().all()


async def get_players_by_slugs(
        db: AsyncSession, kicker_slug: str, target_slug: str
) -> dict[str, Player]:
    result = await db.execute(
        select(Player).where(Player.slug.in_([kicker_slug, target_slug]))
    )
    players = result.scalars().all()
    return {p.slug: p for p in players}


def player_has_shields(p: Player) -> bool:
    return (p.shield_stacks or 0) > 0


def player_has_shit(p: Player) -> bool:
    return (p.shit_stacks or 0) > 0


def dec_shield(p: Player) -> None:
    p.shield_stacks = max(0, (p.shield_stacks or 0) - 1)


def inc_shield(p: Player, count: int) -> None:
    p.shield_stacks = max(0, (p.shield_stacks or 0) + count)


def inc_shit(p: Player, count: int) -> None:
    p.shit_stacks = max(0, (p.shit_stacks or 0) + count)


async def create_shit_kick_move(
        db: AsyncSession,
        *,
        victim_slug: str,
        from_player_slug: str,
        dice: int,
        dice_roll_id: int
) -> None:
    last = await get_players_latest_moves(db, slugs=[victim_slug])
    last_move = last.get(victim_slug)
    cell_from = int(last_move.cell_to) if last_move else 0
    cell_to = max(0, cell_from - dice)

    move = PlayerMove(
        player_slug=victim_slug,
        type=PlayerMoveType.SHIT_KICK.value,
        item_title="",
        item_review="",
        item_rating=0.0,
        item_duration=0,
        item_length=None,
        vod_links=None,
        game_id=None,
        cover_image_url=None,
        difficulty_level=0,
        cell_from=cell_from,
        cell_to=cell_to,
        dice_roll_id=dice_roll_id,
        dice_roll_sum=dice,
        dice_roll=str([dice]),
        from_player_slug=from_player_slug,
    )
    db.add(move)


async def process_kick_logic(
        db: AsyncSession,
        *,
        kicker: Player,
        target: Player,
        success: bool,
        dice: int,
        dice_roll_id: int
) -> tuple[int, PlayerKickResult]:
    if not player_has_shit(kicker):
        return 0, PlayerKickResult.OUT_OF_SHIT

    inc_shit(kicker, -1)

    if success:
        if player_has_shields(target):
            dec_shield(target)
            return dice, PlayerKickResult.SHIELD_REMOVED

        await create_shit_kick_move(
            db, victim_slug=target.slug, from_player_slug=kicker.slug, dice=dice, dice_roll_id=dice_roll_id
        )
        return dice, PlayerKickResult.WIN

    if not player_has_shields(kicker):
        await create_shit_kick_move(
            db, victim_slug=kicker.slug, from_player_slug=kicker.slug, dice=dice, dice_roll_id=dice_roll_id
        )
        return dice, PlayerKickResult.LOSE
    else:
        dec_shield(kicker)
        return dice, PlayerKickResult.LOSE_WITH_SHIELD
