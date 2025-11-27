from __future__ import annotations

from typing import TypedDict

from sqlalchemy import (
    Float,
    and_,  # pyright: ignore[reportUnknownVariableType]
    case,
    cast,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_models import Player, PlayerMove
from src.enums import GameLength, PlayerKickResult, PlayerMoveType


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


class AchievementCounts(TypedDict):
    first: int
    regular: int


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

    games_0_4 = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_0_4.value,
            ),
            else_=0,
        )
    ).label("games_0_4")

    games_5_10 = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_5_10.value,
            ),
            else_=0,
        )
    ).label("games_5_10")

    games_11_16 = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_11_16.value,
            ),
            else_=0,
        )
    ).label("games_11_16")

    games_17_24 = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_17_24.value,
            ),
            else_=0,
        )
    ).label("games_17_24")

    games_25_40 = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_25_40.value,
            ),
            else_=0,
        )
    ).label("games_25_40")

    games_40_plus = func.sum(
        case(
            and_(
                pm.type == PlayerMoveType.COMPLETED.value,
                pm.item_length == GameLength.T_40_PLUS.value,
            ),
            else_=0,
        )
    ).label("games_40_plus")

    dr = cast(pm.dice_roll_sum, Float)
    average_move = func.avg(
        case((pm.type != PlayerMoveType.REROLL.value, func.abs(dr)), else_=None)
    ).label("average_move")

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
            games_0_4,
            games_5_10,
            games_11_16,
            games_17_24,
            games_25_40,
            games_40_plus,
            average_move,
            # average_dice_roll,
            # func.avg(per_row_avg.c.avg_roll_per_row).label("average_dice_roll"),
            ladders_moves_sum,
            snakes_moves_sum,
        )
        .select_from(pm)
        .group_by(pm.player_slug)
    )

    res = await db.execute(q)
    rows = res.mappings().all()

    avg_query = (
        select(text("pm.player_slug"), text("AVG(jt.roll_value) AS average_dice_roll"))
        .select_from(
            text(
                "player_moves pm "
                + "JOIN JSON_TABLE(pm.dice_roll, '$[*]' "
                + "COLUMNS (roll_value DOUBLE PATH '$')) AS jt ON TRUE"
            )
        )
        .group_by(text("pm.player_slug"))
    )

    res = await db.execute(avg_query)
    avg_results = res.mappings().all()
    avg_roll_by_player = {
        r["player_slug"]: round(r["average_dice_roll"], 2)  # pyright: ignore[reportAny]
        for r in avg_results
    }

    # achievements for previous events, don't count in scores
    excluded_achievements = [162, 165, 138, 135, 132, 129]

    unlocked_achievements_query = (
        select(text("player_slug"), text("is_first"), func.count("*").label("count"))
        .select_from(text("player_achievements"))
        .where(
            text(
                f"achievement_id NOT IN ({', '.join(map(str, excluded_achievements))})"
            )
        )
        .group_by(text("player_slug"), text("is_first"))
    )

    # unlocked_achievements_query = (
    #     select(text("player_slug"), text("is_first"), func.count("*").label("count"))
    #     .select_from(text("player_achievements"))
    #     .group_by(text("player_slug"), text("is_first"))
    # )

    unlocked_achievements = await db.execute(unlocked_achievements_query)
    achievement_counts = unlocked_achievements.mappings().all()

    achievements_by_player: dict[str, AchievementCounts] = {}
    for record in achievement_counts:
        slug = record["player_slug"]
        is_first = record["is_first"]
        count = record["count"]
        if slug not in achievements_by_player:
            achievements_by_player[slug] = {"first": 0, "regular": 0}
        if is_first:
            achievements_by_player[slug]["first"] = count
        else:
            achievements_by_player[slug]["regular"] = count

    # print("DEBUG")
    # print(achievement_counts)
    # print(achievements_by_player)

    return [
        {
            **dict(r),
            "map_position": int(map_pos_by_slug.get(r["player_slug"], 0)),  # pyright: ignore[reportAny]
            "average_dice_roll": avg_roll_by_player.get(r["player_slug"], 0.0),
            "first_achievements": achievements_by_player.get(r["player_slug"], {}).get(
                "first", 0
            ),
            "regular_achievements": achievements_by_player.get(
                r["player_slug"], {}
            ).get("regular", 0),
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
    players: list[Player] = result.scalars().all()
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

async def process_kick_logic(
    *,
    kicker: Player,
    target: Player,
) -> PlayerKickResult:
    if not player_has_shit(kicker):
        return PlayerKickResult.OUT_OF_SHIT

    inc_shit(kicker, -1)

    if player_has_shields(target):
        dec_shield(target)
        return PlayerKickResult.SHIELD_REMOVED

    return PlayerKickResult.WIN
