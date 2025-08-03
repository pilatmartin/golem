from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.db.models.user import User
from app.db.repositories.user import UserRepository

SECRET_KEY = "my very secret key"  # TODO: move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# handles password hashing (using bcrypt library)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# handles JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends(),
                            user_repository: UserRepository = Depends(UserRepository)) -> User | None:
    user = await user_repository.get(username=form_data.username)
    print(user)

    if not user:
        return None

    if not verify_password(form_data.password, user.hashed_password):
        return None

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme),
                           user_repository: UserRepository = Depends(UserRepository)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        print("username: ", username)

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repository.get(username=username)
    if user is None:
        raise credentials_exception

    return user
