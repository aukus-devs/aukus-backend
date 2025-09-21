from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_models import PlayerMove


async def get_players_latest_moves(
    db: AsyncSession, *, slugs: list[str]
) -> dict[str, PlayerMove]:
    # Subquery: rank moves per player by id
    stmt = select(
        PlayerMove,
        func.row_number()
        .over(partition_by=PlayerMove.player_slug, order_by=PlayerMove.id.desc())
        .label("rnk"),
    ).subquery()

    # Select only the latest (row_number = 1)
    latest_moves = select(PlayerMove).from_statement(  # pyright: ignore[reportAny]
        select(stmt.c.id, stmt.c.player_slug, stmt.c.rnk).where(stmt.c.rnk == 1)
    )
    result = await db.execute(
        latest_moves.where(PlayerMove.player_slug.in_(slugs))  # pyright: ignore[reportAny]
    )
    moves: list[PlayerMove] = result.scalars().all()
    return {move.player_slug: move for move in moves}
