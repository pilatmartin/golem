import uuid

from fastapi import Depends
from sqlalchemy.sql.operators import exists
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import db
from app.db.models.group import OrganismGroup, Group, UserGroup
from app.db.models.organism import Organism
from app.schemas.base import BaseSchema


class Filters(BaseSchema):
    """
    Filters for organisms.
    """

    user_id: uuid.UUID | None = None
    include_public: bool = True


class OrganismRepository:
    """
    A repository for user management.
    """

    def __init__(self, session: AsyncSession = Depends(db.get_session)) -> None:
        self.session = session

    async def get(self, filters: Filters = None) -> list[Organism]:
        """
        Get a list of filtered organisms.

        Args:
            filters (Filters | None): Filters to apply.

        Returns:
            list[Organism] | None: The list of organisms matching the filters.

        """

        filters = filters or Filters()
        group_ids = []

        if filters.user_id is not None:
            user_groups = (await self.session.execute(
                select(UserGroup)
                .where(UserGroup.user_id == filters.user_id)
            )).scalars().all()
            group_ids = [group.group_id for group in user_groups]

        statement = (
            select(Organism)
            .distinct(Organism.id)
            .join(OrganismGroup, OrganismGroup.organism_id == Organism.id, isouter=True)
            .where(
                or_(
                    OrganismGroup.group_id.in_(group_ids),
                    filters.include_public and Organism.public == True
                )
            )
        )
        organisms = await self.session.execute(statement)

        return organisms.scalars().all()

    async def create(self, organism: Organism) -> Organism:
        """
        Create a new organism.

        Args:
            organism (Organism): The organism to create.

        Returns:
            Organism: The created organism.
        """

        self.session.add(organism)
        await self.session.commit()
        await self.session.refresh(organism)

        return organism
