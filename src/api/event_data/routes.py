from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from src.api.event_data.models import (
    AchievementItem,
    EventDataResponse,
    PlayerItem,
    SkinItem,
)
from src.db.db_models import Player
from src.db.db_session import get_db

router = APIRouter(tags=["event_data"])


@router.get("/api/event_data", response_model=EventDataResponse)
async def get_event_data(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event_settings: dict[str, int | str | None] = {}

    players_query = await db.execute(select(Player))
    players_raw: list[Player] = players_query.scalars().all()
    players: list[PlayerItem] = []
    for player in players_raw:
        players.append(
            PlayerItem(
                slug=player.slug,
                map_position=0,
                equipped_skins=[],
                unlocked_achievements=[],
            )
        )

    skins: list[SkinItem] = []
    achievements: list[AchievementItem] = []

    return EventDataResponse(
        players=players,
        skins=skins,
        achievements=achievements,
        event_settings=event_settings,
    )
