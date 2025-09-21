from collections.abc import Iterable
from typing import cast
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


async def get_next_player_file_id(db: AsyncSession) -> int:
    q = select(func.coalesce(func.max(PlayerFile.id), 0) + 1)
    result = (await db.execute(q)).scalar_one()  # pyright: ignore[reportAny]
    return cast(int, result)


async def get_top_z_for_player(db: AsyncSession, player_slug: str) -> int:
    q = select(func.coalesce(func.max(PlayerFile.z_index), 0)).where(
        PlayerFile.player_slug == player_slug
    )
    result = (await db.execute(q)).scalar_one()  # pyright: ignore[reportAny]
    return cast(int, result)


async def get_player_file(
    db: AsyncSession, *, id: int, player_slug: str
) -> PlayerFile | None:
    res = await db.execute(
        select(PlayerFile).where(
            PlayerFile.id == id, PlayerFile.player_slug == player_slug
        )
    )
    return res.scalars().first()


async def create_player_file(
    db: AsyncSession,
    *,
    id: int,
    player_slug: str,
    url: str,
    width: float,
    height: float,
    rotation: float = 0.0,
    x: float = 0.0,
    y: float = 0.0,
    z_index: int = 0,
    scale_x: int = 1,
    scale_y: int = 1,
) -> PlayerFile:
    row = PlayerFile(
        id=id,
        player_slug=player_slug,
        rotation=rotation,
        x=x,
        y=y,
        url=url,
        width=width,
        height=height,
        z_index=z_index,
        scale_x=scale_x,
        scale_y=scale_y,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_player_file_fields(
    db: AsyncSession,
    *,
    id: int,
    player_slug: str,
    rotation: float,
    x: float,
    y: float,
    width: float,
    height: float,
    z_index: int,
    scale_x: int,
    scale_y: int,
) -> bool:
    pf = await get_player_file(db, id=id, player_slug=player_slug)
    if not pf:
        return False

    pf.rotation = rotation
    pf.x = x
    pf.y = y
    pf.width = width
    pf.height = height
    pf.z_index = z_index
    pf.scale_x = scale_x
    pf.scale_y = scale_y

    # тут без commit — пусть батч коммитит вызывающий код
    await db.flush()
    return True


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
