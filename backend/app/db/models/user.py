import uuid

from sqlmodel import SQLModel, Field, Relationship

from app.db.models.group import Group, UserGroup


class User(SQLModel, table=True):
    """A user of the GOLEM application."""

    __tablename__ = "users"

    id: uuid.UUID = Field(default=uuid.uuid4(), primary_key=True)
    username: str
    hashed_password: str

    groups: list[Group] = Relationship(back_populates="users", link_model=UserGroup,
                                       sa_relationship_kwargs={"lazy": "selectin"})
