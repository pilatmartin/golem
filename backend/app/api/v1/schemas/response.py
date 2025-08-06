from typing import Literal

from app.schemas.base import BaseSchema


class ResponseSingle[T](BaseSchema):
    """Success API Response schema for single object."""

    success: Literal[True] = True
    data: T


# TODO: add pagination
class ResponseList[T](BaseSchema):
    """Success API Response schema for a list of objects."""

    success: Literal[True] = True
    data: list[T]


class ErrorResponse(BaseSchema):
    """Error API Response schema."""

    success: Literal[False] = False
    message: str
