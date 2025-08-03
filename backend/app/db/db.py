from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import app_config

engine = create_async_engine(app_config.database_url, echo=True, future=True)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
