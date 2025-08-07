import uuid

from sqlmodel import SQLModel, Field, Relationship


class OrganismGroup(SQLModel, table=True):
    """Many-to-many relationship between organisms and groups."""

    __tablename__ = "organisms_groups"

    organism_id: uuid.UUID = Field(foreign_key="organisms.id", primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="groups.id", primary_key=True)


class UserGroup(SQLModel, table=True):
    """Many-to-many relationship between users and groups."""

    __tablename__ = "users_groups"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="groups.id", primary_key=True)


class Group(SQLModel, table=True):
    """A group of users, which share data."""

    __tablename__ = "groups"

    id: uuid.UUID = Field(default=uuid.uuid4(), primary_key=True)
    name: str

    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroup)
    organisms: list["Organism"] = Relationship(back_populates="groups", link_model=OrganismGroup)
