from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_models import Player
from src.db.db_session import get_db
from src.enums import UserRole
from src.utils.jwt import decode_access_token

security = HTTPBearer()


class TokenPayload(BaseModel):
    slug: str
    exp: int


def parse_token(token: str) -> TokenPayload:
    try:
        payload = decode_access_token(token)
        parsed = TokenPayload.model_validate(payload)
        return parsed
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_player(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    for_update: bool = False,
    allow_acting: bool = True,
):
    token = credentials.credentials
    payload = parse_token(token)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if payload.exp < now_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    # Fetch the user making the request
    query = select(Player).where(Player.slug == payload.slug)
    result = await db.execute(query)
    requesting_player: Player | None = result.scalars().first()

    if requesting_player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # Check if an admin is acting as another user
    acting_user_id_str = request.headers.get("x-acting-user-id")
    is_acting = (
        allow_acting
        and requesting_player.role == UserRole.ADMIN.value
        and acting_user_id_str
    )

    if is_acting and acting_user_id_str:
        # If acting, fetch the target user, applying a lock if necessary
        target_query = select(Player).where(Player.id == int(acting_user_id_str))
        if for_update:
            target_query = target_query.with_for_update()

        target_result = await db.execute(target_query)
        target_player = target_result.scalars().first()

        if target_player is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Acting player not found",
            )
        return target_player

    # If not acting, but a lock is requested for the original user
    if for_update:
        # Re-fetch the original user with a lock
        locked_query = (
            select(Player).where(Player.id == requesting_player.id).with_for_update()
        )
        locked_result = await db.execute(locked_query)
        # The user must exist, so we can safely return it
        return locked_result.scalars().first()

    # Otherwise, return the user we already fetched
    return requesting_player


async def get_current_player_for_update(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    return await get_current_player(request, credentials, db, for_update=True)


async def get_current_player_direct(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    return await get_current_player(request, credentials, db, allow_acting=False)
