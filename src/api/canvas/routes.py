from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db_session import get_db
from src.db.db_models import PlayerFile, User
from src.utils.auth import get_current_user_for_update
from src.api.canvas.models import CanvasFile, CanvasUpdateRequest
# from boto_s3 import upload_file_s3, delete_file_s3

router = APIRouter(tags=["canvas"])


@router.get("/api/canvas/{player_id}", response_model=List[CanvasFile])
async def get_canvas_files(
    player_id: int,
    current_user: Annotated[User, Depends(get_current_user_for_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(PlayerFile)
        .where(PlayerFile.player_id == player_id)
        .order_by(PlayerFile.z_index.asc(), PlayerFile.id.asc())
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    return [CanvasFile.model_validate(r) for r in rows]


@router.post("/api/canvas/{player_id}/upload", response_model=CanvasFile, status_code=status.HTTP_201_CREATED)
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

    next_id = (await db.execute(select(func.coalesce(func.max(PlayerFile.id), 0) + 1))).scalar_one()

    s3_key = f"{player_id}-{next_id}-{file.filename}"
    # url, s3error = upload_file_s3(file.file, s3_key)
    # if s3error:
    #     raise HTTPException(status_code=500, detail=f"Error upload file to s3: {s3error}")

    top_z = (
        await db.execute(
            select(func.coalesce(func.max(PlayerFile.z_index), 0)).where(
                PlayerFile.player_id == player_id
            )
        )
    ).scalar_one()

    row = PlayerFile(
        id=next_id,
        player_id=player_id,
        rotation=0.0,
        x=0.0,
        y=0.0,
        url='https://aboba.ru',
        width=width,
        height=height,
        z_index=top_z + 1,
        scale_x=1,
        scale_y=1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
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

        q = select(PlayerFile).where(
            PlayerFile.id == item.id, PlayerFile.player_id == player_id
        )
        res = await db.execute(q)
        pf = res.scalars().first()
        if not pf:
            raise HTTPException(status_code=404, detail=f"File {item.id} not found")

        pf.rotation = item.rotation
        pf.x = item.x
        pf.y = item.y
        pf.width = item.width
        pf.height = item.height
        pf.z_index = item.z_index
        pf.scale_x = item.scale_x
        pf.scale_y = item.scale_y

    if payload.delete_ids:
        q = select(PlayerFile).where(
            PlayerFile.id.in_(payload.delete_ids), PlayerFile.player_id == player_id
        )
        res = await db.execute(q)
        rows = res.scalars().all()
        for r in rows:
            key = getattr(r, "s3_file_id", None)
            # if key:
            #     try:
            #         delete_file_s3(key)
            #     except Exception:
            #         pass
            await db.delete(r)

    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
