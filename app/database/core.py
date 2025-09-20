from typing import Any

from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker,
    AsyncSession, AsyncEngine
)

from config_reader import settings


class DatabaseManager:
    def __init__(self, db_url: str, **kwargs: Any):
        self.engine: AsyncEngine = create_async_engine(
            db_url,
            **kwargs
        )
        self.session_maker: async_sessionmaker[
            AsyncSession
        ] = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def dispose(self):
        await self.engine.dispose()
        print('Database connection closed')


db_manager = DatabaseManager(
    settings.db_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)