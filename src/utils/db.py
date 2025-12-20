import logging
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def safe_commit(session: AsyncSession):
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database error in safe_commit: {e}", exc_info=True)
        raise


# async def log_error_to_db(
#     session: AsyncSession,
#     error: Exception,
#     function_name: str,
#     player_id: int | None = None,
#     context: str | None = None,
# ):
#     from src.db.db_models import ErrorLog

#     error_log = ErrorLog(
#         player_id=player_id,
#         error_type=getattr(type(error), "__name__", "UnknownError"),
#         error_message=str(error),
#         function_name=function_name,
#         context=context,
#     )

#     session.add(error_log)
#     await safe_commit(session)


async def reset_database(db: AsyncSession):
    from src.db.db_models import (
        PlayerMove,
    )

    # reset rules to the before specific date
    # rules_max_ids_by_category_query = select(
    #     Rules.category, func.max(Rules.id).label("max_id")
    # ).group_by(Rules.category)

    # delete_to_date = datetime(2025, 8, 14, 0, 0, tzinfo=timezone.utc)
    # date_ts = int(delete_to_date.timestamp())

    # rules_by_category = await db.execute(rules_max_ids_by_category_query)
    # for category, max_id in rules_by_category:
    #     if max_id is not None:
    #         delete_rules_query = delete(Rules).where(
    #             Rules.category == category,
    #             Rules.id != max_id,
    #             Rules.created_at < date_ts,
    #         )
    #         await db.execute(delete_rules_query)

    print("resetting")

    delete_moves = delete(PlayerMove)
    _ = await db.execute(delete_moves)
