# setup_db_async.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.db_models import DbBase
from src.config import DATABASE_URL

async def setup_db():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(DbBase.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_db())
    print(f"Database created at {DATABASE_URL}")
