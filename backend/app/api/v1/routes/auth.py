from datetime import timedelta

from fastapi import APIRouter, Depends, status, HTTPException
from starlette.responses import JSONResponse

from app.api.v1.schemas.auth import LoginResponse, UserResponse, LoginRequest
from app.api.v1.schemas.response import ResponseSingle
from app.config import app_config
from app.db.models.user import User
from app.db.repositories.user import UserRepository
from app.services.auth import (
    authenticate_user,
    get_password_hash,
    get_current_user,
    create_access_token
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login")
async def login(user: User = Depends(authenticate_user)) -> JSONResponse:
    """
    Login a user.

    Fails if the user does not exist or the password is incorrect.
    Returns the access token and the token type.
    """

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=app_config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    data = LoginResponse(access_token=access_token, token_type="bearer")
    content = ResponseSingle(data=data)

    response = JSONResponse(content=content.model_dump())
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return response


@auth_router.post("/register")
async def register(login_data: LoginRequest, user_repository: UserRepository = Depends(UserRepository)):
    if await user_repository.get(username=login_data.username):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = get_password_hash(login_data.password)
    user = await user_repository.create(User(username=login_data.username, hashed_password=hashed_password))
    user_response = UserResponse.model_validate(user)

    return ResponseSingle(data=user_response)


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    user_response = UserResponse.model_validate(user)

    return ResponseSingle(data=user_response)
