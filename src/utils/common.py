from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select


from src.db.db_models import EventSettings
from src.enums import (
    EventSetting,
)


async def get_event_setting(db: AsyncSession, setting: EventSetting) -> str | None:
    query = select(EventSettings).where(EventSettings.key_name == setting.value)
    result = await db.execute(query)
    db_setting: EventSettings | None = result.scalar_one_or_none()
    if db_setting:
        return db_setting.value
    return None
