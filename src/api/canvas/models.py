from typing import ClassVar
from pydantic.config import ConfigDict

from src.api.utils import ApiModel


class CanvasFile(ApiModel):
    id: int
    rotation: float
    x: float
    y: float
    url: str
    width: float
    height: float
    z_index: int
    scale_x: float
    scale_y: float
    attach_move_id: int | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True, from_attributes=True
    )


class CanvasUpdateRequest(ApiModel):
    files: list[CanvasFile]
    delete_ids: list[int] | None = None


class CanvasFilesResponse(ApiModel):
    files: list[CanvasFile]
