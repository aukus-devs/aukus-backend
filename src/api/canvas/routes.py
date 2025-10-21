from sqlalchemy import select
from src.utils.boto_s3 import upload_file_s3, delete_file_s3  # pyright: ignore[reportUnknownVariableType]

from typing import Annotated
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

from src.config import IS_LOCAL
from src.db.db_session import get_db
from src.db.db_models import Player, PlayerFile
from src.utils.auth import get_current_player
from src.api.canvas.models import CanvasFile, CanvasFilesResponse, CanvasUpdateRequest

from src.db.queries.player_files import (
    get_player_files,
    get_top_z_for_player,
    delete_player_files,
)
from src.utils.common import gen_id

router = APIRouter(tags=["canvas"])


@router.get("/api/canvas/{player_slug}", response_model=CanvasFilesResponse)
async def get_canvas_files(
    player_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = await get_player_files(db, player_slug)
    return {"files": rows}


@router.post(
    "/api/canvas/{player_slug}/upload",
    response_model=CanvasFile,
    status_code=status.HTTP_201_CREATED,
)
async def upload_canvas_image(
    player_slug: str,
    current_user: Annotated[Player, Depends(get_current_player)],  # pyright: ignore[reportUnusedParameter]
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),  # pyright: ignore[reportCallInDefaultInitializer]
    width: float = Form(...),  # pyright: ignore[reportCallInDefaultInitializer]
    height: float = Form(...),  # pyright: ignore[reportCallInDefaultInitializer]
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file found")

    top_z = await get_top_z_for_player(db, player_slug)

    short_id = gen_id(file.filename)
    s3_file_id = f"{player_slug}-{file.filename}-{short_id}"

    if IS_LOCAL:
        # Локальная заглушка вместо S3
        uploaded_url = "https://thumbs.dreamstime.com/b/demo-red-rubber-stamp-over-white-background-88003515.jpg"
    else:
        (uploaded_url, error) = await upload_file_s3(file, s3_file_id)
        if error:
            raise HTTPException(status_code=500, detail=f"File upload error: {error}")

    if not uploaded_url:
        raise HTTPException(status_code=500, detail="File upload failed")

    row = PlayerFile(
        s3_file_id=s3_file_id,
        player_slug=player_slug,
        rotation=0,
        x=100,
        y=100,
        url=uploaded_url,
        width=width,
        height=height,
        z_index=top_z + 1,
        scale_x=1,
        scale_y=1,
    )
    db.add(row)
    await db.flush()
    return CanvasFile.model_validate(row)


@router.put("/api/canvas/{player_slug}/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_canvas(
    player_slug: str,
    payload: CanvasUpdateRequest,
    current_user: Annotated[Player, Depends(get_current_player)],  # pyright: ignore[reportUnusedParameter]
    db: Annotated[AsyncSession, Depends(get_db)],
):
    files_ids = [item.id for item in payload.files]
    existing_files_query = await db.execute(
        select(PlayerFile).where(
            PlayerFile.player_slug == player_slug, PlayerFile.id.in_(files_ids)
        )
    )
    existing_files: list[PlayerFile] = existing_files_query.scalars().all()
    existing_files_by_id = {file.id: file for file in existing_files}

    for item in payload.files:
        file = existing_files_by_id.get(item.id)
        if not file:
            raise HTTPException(status_code=404, detail=f"File {item.id} not found")

        file.rotation = item.rotation
        file.x = item.x
        file.y = item.y
        file.width = item.width
        file.height = item.height
        file.z_index = item.z_index
        file.scale_x = item.scale_x
        file.scale_y = item.scale_y

    if payload.delete_ids:
        for file_id in payload.delete_ids:
            file = existing_files_by_id.get(file_id)
            if file:
                _ = delete_file_s3(file.s3_file_id)
        _ = await delete_player_files(
            db, player_slug=player_slug, ids=payload.delete_ids
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
