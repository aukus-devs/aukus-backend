from typing import ClassVar
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class CanvasFile(BaseModel):
    id: int
    rotation: float
    x: float
    y: float
    url: str
    width: float
    height: float
    z_index: int = Field(alias="zIndex")
    scale_x: int = Field(alias="scaleX")
    scale_y: int = Field(alias="scaleY")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True, from_attributes=True
    )


class CanvasUpdateRequest(BaseModel):
    files: list[CanvasFile]
    delete_ids: list[int] | None = None


class CanvasFilesResponse(BaseModel):
    files: list[CanvasFile]
