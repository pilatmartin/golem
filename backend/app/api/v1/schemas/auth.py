import uuid

from app.schemas.base import BaseSchema


class LoginResponse(BaseSchema):
    access_token: str
    token_type: str

class GroupResponse(BaseSchema):
    id: uuid.UUID
    name: str

class UserResponse(BaseSchema):
    id: uuid.UUID
    username: str
    groups: list[GroupResponse]