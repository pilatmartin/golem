import uuid

from sqlmodel import SQLModel, Field, Relationship

from app.db.models.group import Group, OrganismGroup


class Organism(SQLModel, table=True):
    """An organism on which analysis can be performed."""

    __tablename__ = "organisms"

    id: uuid.UUID = Field(default=uuid.uuid4(), primary_key=True)
    name: str
    filename: str
    public: bool

    groups: list[Group] = Relationship(back_populates="organisms", link_model=OrganismGroup,
                                       sa_relationship_kwargs={"lazy": "selectin"})
