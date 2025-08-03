from datetime import timedelta

from fastapi import APIRouter, Depends, status, HTTPException

from app.db.models.user import User
from app.services.auth import authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, \
    get_password_hash

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login")
async def login(user: User = Depends(authenticate_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


# TODO: remove
@auth_router.post("/hash")
async def get_hash(password: str):
    return get_password_hash(password)
