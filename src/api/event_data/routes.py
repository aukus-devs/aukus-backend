from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from src.api.event_data.models import (
    AchievementItem,
    EventDataResponse,
    PlayerItem,
    SkinItem,
    UnlockedAchievementItem,
)
from src.api.player.utils import get_dice_options
from src.db.db_models import (
    Achievement,
    EventSettings,
    Player,
    PlayerAchievement,
    PlayerSkin,
    Skin,
)
from src.db.db_session import get_db
from src.db.queries.player_moves import get_players_latest_moves
from src.db.utils import model_to_dict
from src.enums import AchievementVisibility, DiceOption
from src.utils.auth import get_current_player_or_none

router = APIRouter(tags=["event_data"])


@router.get("/api/event_data", response_model=EventDataResponse)
async def get_event_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player | None, Depends(get_current_player_or_none)],
):
    event_settings: dict[str, int | str | None] = {}
    event_settings_query = await db.execute(select(EventSettings))
    event_settings_raw: list[EventSettings] = event_settings_query.scalars().all()
    for setting in event_settings_raw:
        event_settings[setting.key_name] = setting.value

    players_query = await db.execute(select(Player))
    players_raw: list[Player] = players_query.scalars().all()

    player_skins_query = await db.execute(select(PlayerSkin))
    player_skins_all: list[PlayerSkin] = player_skins_query.scalars().all()

    unlocked_achievements_query = await db.execute(select(PlayerAchievement))
    unlocked_achievements: list[PlayerAchievement] = (
        unlocked_achievements_query.scalars().all()
    )

    players_slugs = [player.slug for player in players_raw]
    players_last_moves = await get_players_latest_moves(db, slugs=players_slugs)

    players: list[PlayerItem] = []
    for player in players_raw:
        player_skins = [
            skin for skin in player_skins_all if skin.player_slug == player.slug
        ]
        equipped_ids = [skin.skin_id for skin in player_skins if skin.is_equipped]
        player_skins_ids = [skin.skin_id for skin in player_skins]

        player_achievements = [
            UnlockedAchievementItem(
                id=achievement.achievement_id, unlocked_at=achievement.created_at
            )
            for achievement in unlocked_achievements
            if achievement.player_slug == player.slug
        ]
        last_move = players_last_moves.get(player.slug)
        map_position = last_move.cell_to if last_move else 0

        players.append(
            PlayerItem(
                slug=player.slug,
                map_position=map_position,
                equipped_skins=equipped_ids,
                available_skins=player_skins_ids,
                unlocked_achievements=player_achievements,
                color=player.color,
                last_move=last_move,
            )
        )

    skins_query = await db.execute(select(Skin))
    skins_raw: list[Skin] = skins_query.scalars().all()
    skins = [SkinItem.model_validate(skin) for skin in skins_raw]

    unlocked_achievements_by_id = {a.id: a for a in unlocked_achievements}

    achievements_query = await db.execute(select(Achievement).order_by(Achievement.id))
    achievements_raw: list[Achievement] = achievements_query.scalars().all()

    achievements: list[AchievementItem] = []
    for a in achievements_raw:
        visibility = (
            AchievementVisibility.VISIBLE
            if unlocked_achievements_by_id.get(a.id)
            else AchievementVisibility.HIDDEN
        )
        achievements.append(
            AchievementItem(
                id=a.id,
                description="???"
                if visibility == AchievementVisibility.HIDDEN
                else a.description,
                reward_skin_id=a.reward_skin_id,
                visibility=visibility,
            )
        )

    last_move = None
    dice_options: list[DiceOption] = []

    if current_user:
        last_move = players_last_moves.get(current_user.slug)
        if last_move:
            dice_options = get_dice_options(last_move)

    return EventDataResponse(
        players=players,
        skins=skins,
        achievements=achievements,
        event_settings=event_settings,
        dice_options=dice_options,
    )
