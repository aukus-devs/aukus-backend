from src.db.db_models import ShitKicks
from sqlalchemy.ext.asyncio import AsyncSession


async def create_kick_shit_event(
        db: AsyncSession,
        player_slug: str,
        target_slug: str=None,
        result: str=None,
) -> None:
    event = ShitKicks(
        player_slug=player_slug,
        target_player_slug=target_slug,
        result=result,
    )

    db.add(event)
