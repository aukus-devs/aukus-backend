from typing import ClassVar
from pydantic import Field
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
    z_index: int = Field(alias="zIndex")
    scale_x: float = Field(alias="scaleX")
    scale_y: float = Field(alias="scaleY")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True, from_attributes=True
    )


class CanvasUpdateRequest(ApiModel):
    files: list[CanvasFile]
    delete_ids: list[int] | None = None


class CanvasFilesResponse(ApiModel):
    files: list[CanvasFile]
