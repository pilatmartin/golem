from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.db.models.user import User
from app.db.repositories.user import UserRepository
from app.config import app_config

# handles password hashing (using bcrypt, TODO: consider argon2)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# handles JWT token authentication
jwt_scheme = HTTPBearer(auto_error=False)


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


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(jwt_scheme),
                           user_repository: UserRepository = Depends(UserRepository)) -> User:
    """
    Get the current user based on the token.

    Throws:
        HTTPException: If the token is invalid.

    Returns:
        User: The current user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload: dict = jwt.decode(token.credentials, app_config.secret_key, algorithms=[app_config.algorithm])
        username: str | None = payload.get("sub")

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repository.get(username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(token: HTTPAuthorizationCredentials = Depends(jwt_scheme),
                                    user_repository: UserRepository = Depends(UserRepository)) -> User | None:
    """
    Get the current user based on the token without throwing an exception.

    Returns:
        User | None: The current user if logged in, None otherwise.
    """

    try:
        current_user = await get_current_user(token=token, user_repository=user_repository)
        return current_user
    except HTTPException:
        return None
