import uuid

from app.schemas.base import BaseSchema


class LoginResponse(BaseSchema):
    """Response schema for login endpoint."""

    access_token: str
    token_type: str

class GroupResponse(BaseSchema):
    """Response schema for a user group."""

    id: uuid.UUID
    name: str

class UserResponse(BaseSchema):
    """Response schema for a user."""

    id: uuid.UUID
    username: str
    groups: list[GroupResponse]