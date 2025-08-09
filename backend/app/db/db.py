from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import app_config

engine = create_async_engine(app_config.database_url, echo=True, future=True)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Database session generator."""

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


async def add_default_admin() -> None:
    from app.db.models.user import User
    from app.db.repositories.user import UserRepository
    from app.services.auth import get_password_hash

    async for session in get_session():
        user_repository = UserRepository(session=session)
        await user_repository.create(
            User(
                username=app_config.default_admin_username,
                hashed_password=get_password_hash(app_config.default_admin_password),
            )
        )
