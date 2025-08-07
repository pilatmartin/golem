import uuid

from app.api.v1.schemas.auth import GroupResponse
from app.schemas.base import BaseSchema


class OrganismResponse(BaseSchema):
    """Response schema for organism endpoints."""

    id: uuid.UUID
    name: str
    filename: str
    public: bool
    groups: list[GroupResponse]
