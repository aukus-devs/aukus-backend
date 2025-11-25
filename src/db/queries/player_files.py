from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, select

from src.db.db_models import PlayerFile


async def get_player_files(db: AsyncSession, player_slug: str) -> list[PlayerFile]:
    res = await db.execute(
        select(PlayerFile)
        .where(PlayerFile.player_slug == player_slug)
        .order_by(PlayerFile.z_index.asc(), PlayerFile.id.asc())
    )
    return res.scalars().all()


async def get_top_z_for_player(db: AsyncSession, player_slug: str) -> int:
    q = select(func.coalesce(func.max(PlayerFile.z_index), 0)).where(
        PlayerFile.player_slug == player_slug
    )
    result: int = (await db.execute(q)).scalar_one()  # pyright: ignore[reportAny]
    return result


async def get_player_file(
    db: AsyncSession, *, id: int, player_slug: str
) -> PlayerFile | None:
    res = await db.execute(
        select(PlayerFile).where(
            PlayerFile.id == id, PlayerFile.player_slug == player_slug
        )
    )
    return res.scalars().first()


async def delete_player_files(
    db: AsyncSession, *, player_slug: str, ids: Iterable[int]
) -> list[PlayerFile]:
    res = await db.execute(
        select(PlayerFile).where(
            PlayerFile.id.in_(list(ids)),
            PlayerFile.player_slug == player_slug,
        )
    )
    rows = res.scalars().all()
    for r in rows:  # pyright: ignore[reportAny]
        await db.delete(r)
    await db.flush()
    return rows
