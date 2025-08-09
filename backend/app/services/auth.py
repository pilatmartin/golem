from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.api.v1.oauth2_cookie_scheme import OAuth2PasswordBearerWithCookie
from app.db import db
from app.db.models.user import User
from app.db.repositories.user import UserRepository
from app.config import app_config

# handles password hashing (using bcrypt, TODO: consider argon2)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# handles JWT token authentication via cookie
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/v1/auth/login", auto_error=False)

ADMINISTRATORS_GROUP = "administrators"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the plain password matches the hashed password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """

    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create an access token.

    Args:
        data (dict): The data to include in the access token.
        expires_delta (timedelta, optional): The expiration time for the access token.

    Returns:
        str: The access token.
    """

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, app_config.secret_key, algorithm=app_config.algorithm)

    return encoded_jwt


async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends(),
                            user_repository: UserRepository = Depends(UserRepository)) -> User | None:
    """
    Authenticate a user.

    Verifies if the user exists and if the password is correct.

    Returns:
        User | None: The user if authenticated, None otherwise.
    """

    user = await user_repository.get(username=form_data.username)

    if not user:
        return None

    if not verify_password(form_data.password, user.hashed_password):
        return None

    return user


# TODO: move some logic to the user_loader middleware
async def get_current_user(request: Request, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
                           user_repository: UserRepository = Depends(UserRepository)) -> User:
    """
    Get the current user based on the token.

    Throws:
        HTTPException: If the token is invalid.

    Returns:
        User: The current user.
    """

    if hasattr(request.state, "user") and request.state.user is not None:
        return request.state.user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload: dict = decode_token(token.credentials)
        username: str | None = payload.get("sub")

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # TODO: handle other jwt exceptions

    user = await user_repository.get(username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(request: Request, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
                                    user_repository: UserRepository = Depends(UserRepository)) -> User | None:
    """
    Get the current user based on the token without throwing an exception.

    Returns:
        User | None: The current user if logged in, None otherwise.
    """

    try:
        current_user = await get_current_user(request, token, user_repository)
        return current_user
    except HTTPException:
        return None


async def get_current_admin_user(request: Request, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
                                 user_repository: UserRepository = Depends(UserRepository)) -> User | None:
    """
    Get the current admin user based on the token.

    Throws:
        HTTPException: If the user is not an admin.

    Returns:
        User: The current admin user.
    """

    current_user = await get_current_user(request, token, user_repository)
    if is_admin(current_user):
        return current_user
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


async def get_user_from_token(token: str) -> User | None:
    try:
        payload: dict = decode_token(token)
        username: str | None = payload.get("sub")

        if username is None:
            return None
    except JWTError:
        return None

    async for session in db.get_session():
        user_repository = UserRepository(session=session)
        return await user_repository.get(username=username)
    return None


def is_admin(user: User) -> bool:
    """
    Check if a user is an admin. User is considered an admin if they have the ADMINISTRATORS_GROUP group.

    Args:
        user (User): The user to check.

    Returns:
        bool: True if the user is an admin, False otherwise.
    """
    return user is not None and any(group.name == ADMINISTRATORS_GROUP for group in user.groups)


def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return the payload as a dictionary.

    Args:
        token (str): The JWT token to decode.

    Throws:
        JWTError – If the signature is invalid in any way.
        ExpiredSignatureError – If the signature has expired.
        JWTClaimsError – If any claim is invalid in any way

    Returns:
        dict: The decoded token.
    """
    return jwt.decode(token, app_config.secret_key, algorithms=[app_config.algorithm])
