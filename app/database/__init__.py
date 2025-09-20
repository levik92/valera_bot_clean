from .core import db_manager
from .models import Base


async def create_tables():
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully")