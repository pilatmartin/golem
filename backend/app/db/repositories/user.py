from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import db
from app.db.models.user import User


class UserRepository:
    """
    A repository for user management.
    """

    def __init__(self, session: AsyncSession = Depends(db.get_session)) -> None:
        self.session = session

    async def get(self, username: str) -> User | None:
        """
        Get a single user by username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user if found, None otherwise.

        """

        statement = select(User).where(User.username == username)
        user = await self.session.execute(statement)

        return user.scalars().first()

    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user (User): The user to create.

        Returns:
            User: The created user.
        """

        user_exists = await self.get(user.username)
        if user_exists is not None:
            return user_exists

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user
