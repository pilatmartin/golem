"""Test routes. Will be removed."""

from fastapi import APIRouter

test_router = APIRouter(prefix="/test", tags=["test"])


@test_router.get("/")
async def test():
    return {"message": "test"}
