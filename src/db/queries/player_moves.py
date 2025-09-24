from __future__ import annotations


from sqlalchemy import select, func, case, and_, cast, Float  # pyright: ignore[reportUnknownVariableType]
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_models import Player, PlayerMove


async def get_players_latest_moves(
    db: AsyncSession, *, slugs: list[str] | None = None
) -> dict[str, PlayerMove]:
    # Subquery: rank moves per player by id
    stmt = select(
        PlayerMove,
        func.row_number()
        .over(partition_by=PlayerMove.player_slug, order_by=PlayerMove.id.desc())
        .label("rnk"),
    ).subquery()

    # Select only the latest (row_number = 1)
    query = select(PlayerMove).from_statement(  # pyright: ignore[reportAny]
        select(stmt.c.id, stmt.c.player_slug, stmt.c.rnk).where(stmt.c.rnk == 1)
    )
    if slugs:
        query = query.where(PlayerMove.player_slug.in_(slugs))  # pyright: ignore[reportAny]

    result = await db.execute(query)  # pyright: ignore[reportAny]
    moves: list[PlayerMove] = result.scalars().all()
    return {move.player_slug: move for move in moves}


async def get_players_stats(db: AsyncSession) -> list[dict[str, str | int | float]]:
    pm = PlayerMove

    total_moves = func.count().label("total_moves")
    games_completed = func.sum(case((pm.type == "completed", 1), else_=0)).label(
        "games_completed"
    )
    games_dropped = func.sum(case((pm.type == "drop", 1), else_=0)).label(
        "games_dropped"
    )
    sheikh_moments = func.sum(case((pm.type == "sheikh", 1), else_=0)).label(
        "sheikh_moments"
    )
    rerolls = func.sum(case((pm.type == "reroll", 1), else_=0)).label("rerolls")
    movies = func.sum(case((pm.type == "movie", 1), else_=0)).label("movies")
    ladders = func.sum(case((pm.ladder_from.is_not(None), 1), else_=0)).label("ladders")
    snakes = func.sum(case((pm.snake_from.is_not(None), 1), else_=0)).label("snakes")

    tiny_games = func.sum(
        case(and_(pm.type == "completed", pm.item_length == "tiny"), else_=0)
    ).label("tiny_games")
    short_games = func.sum(
        case(and_(pm.type == "completed", pm.item_length == "short"), else_=0)
    ).label("short_games")
    medium_games = func.sum(
        case(and_(pm.type == "completed", pm.item_length == "medium"), else_=0)
    ).label("medium_games")
    long_games = func.sum(
        case(and_(pm.type == "completed", pm.item_length == "long"), else_=0)
    ).label("long_games")

    dr = cast(pm.dice_roll_sum, Float)
    average_move = func.avg(
        case((pm.type != "reroll", func.abs(dr)), else_=None)
    ).label("average_move")

    average_dice_roll = func.avg(
        case(
            (pm.cell_to > 101, None),
            (pm.item_length.in_(("tiny", "short")), func.abs(dr)),
            (and_(pm.item_length == "medium", pm.cell_from < 81), func.abs(dr / 2.0)),
            (and_(pm.item_length == "long", pm.cell_from < 81), func.abs(dr / 3.0)),
            (and_(pm.cell_from < 81, pm.type.in_(("drop", "sheikh"))), func.abs(dr)),
            (
                and_(pm.cell_from >= 81, pm.item_length.in_(("medium", "long"))),
                func.abs(dr),
            ),
            (
                and_(pm.cell_from >= 81, pm.type.in_(("drop", "sheikh"))),
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
