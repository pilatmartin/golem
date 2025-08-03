from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import db
from app.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(db.get_session)) -> None:
        self.session = session

    async def get(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        user = await self.session.execute(statement)
        return user.scalars().first()
