# from boto_s3 import upload_file_s3, delete_file_s3

from typing import Annotated, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_session import get_db
from src.db.db_models import User
from src.utils.auth import get_current_user_for_update
from src.api.canvas.models import CanvasFile, CanvasUpdateRequest

from src.db.queries.player_files import (
    get_player_files,
    get_next_player_file_id,
    get_top_z_for_player,
    create_player_file,
    update_player_file_fields,
    delete_player_files,
)

router = APIRouter(tags=["canvas"])


@router.get("/api/canvas/{player_id}", response_model=List[CanvasFile])
async def get_canvas_files(
    player_id: int,
    current_user: Annotated[User, Depends(get_current_user_for_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = await get_player_files(db, player_id)
    return [CanvasFile.model_validate(r) for r in rows]


@router.post(
    "/api/canvas/{player_id}/upload",
    response_model=CanvasFile,
    status_code=status.HTTP_201_CREATED,
)
async def upload_canvas_image(
    player_id: int,
    current_user: Annotated[User, Depends(get_current_user_for_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    width: float = Form(...),
    height: float = Form(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file found")

    next_id = await get_next_player_file_id(db)
    top_z = await get_top_z_for_player(db, player_id)

    # Локальная заглушка вместо S3 — можно заменить на реальную загрузку
    url = "https://aboba.ru"

    row = await create_player_file(
        db,
        id=next_id,
        player_id=player_id,
        url=url,
        width=width,
        height=height,
        rotation=0.0,
        x=0.0,
        y=0.0,
        z_index=top_z + 1,
        scale_x=1,
        scale_y=1,
    )
    return CanvasFile.model_validate(row)


@router.put("/api/canvas/{player_id}/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_canvas(
    player_id: int,
    payload: CanvasUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user_for_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    for item in payload.files:
        if item.scale_x > 1 or item.scale_x < -1:
            raise HTTPException(status_code=400, detail="Invalid scale value")
        if item.scale_y > 1 or item.scale_y < -1:
            raise HTTPException(status_code=400, detail="Invalid scale value")

        ok = await update_player_file_fields(
            db,
            id=item.id,
            player_id=player_id,
            rotation=item.rotation,
            x=item.x,
            y=item.y,
            width=item.width,
            height=item.height,
            z_index=item.z_index,
            scale_x=item.scale_x,
            scale_y=item.scale_y,
        )
        if not ok:
            raise HTTPException(status_code=404, detail=f"File {item.id} not found")

    if payload.delete_ids:
        await delete_player_files(db, player_id=player_id, ids=payload.delete_ids)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
