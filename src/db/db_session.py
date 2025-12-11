# database.py
import asyncio
from contextlib import asynccontextmanager
from typing import Callable

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
    create_async_engine,
)

from src.config import DATABASE_URL
from src.db.db_models import (
    DbBase,
)

is_sqlite = DATABASE_URL.startswith("sqlite")


if is_sqlite:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        # connect_args={
        #     "statement_cache_size": 0,
        #     "prepared_statement_cache_size": 0,
        #     "ssl": "require",
        #     "prepared_statement_name_func": make_statement_name,
        # },
    )

SessionLocal: Callable[[], AsyncSession] = async_sessionmaker(  # pyright: ignore[reportUnknownVariableType]
    bind=engine, expire_on_commit=False
)


async def get_db():
    async with SessionLocal() as session:
        max_retries = 3

        try:
            yield session

            for attempt in range(max_retries):
                try:
                    await session.commit()
                    break
                except OperationalError as e:
                    await session.rollback()

                    if "Deadlock found" in str(e) and attempt < max_retries - 1:
                        await asyncio.sleep(0.05 * (attempt + 1))
                        continue
                    raise

        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_readonly():
    async with SessionLocal() as session:
        session.expire_on_commit = False  # pyright: ignore[reportAttributeAccessIssue]
        session.autoflush = False  # pyright: ignore[reportAttributeAccessIssue]
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.rollback()
            await session.close()


@asynccontextmanager
async def get_session():
    async with SessionLocal() as session:
        yield session


async def init_db_async():
    async with engine.begin() as conn:
        await conn.run_sync(DbBase.metadata.create_all)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


if __name__ == "__main__":
    asyncio.run(init_db_async())
    print("Database initialized successfully.")
