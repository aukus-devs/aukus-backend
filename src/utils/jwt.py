from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.hash import bcrypt

from src.config import TOKEN_SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days


def create_access_token(
    data: dict[str, str | int], expires_delta: timedelta | None = None
):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire_ts = int(expire.timestamp())
    to_encode.update({"exp": expire_ts})
    return jwt.encode(to_encode, TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    return jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[ALGORITHM])


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)
