from typing import ClassVar
from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True, from_attributes=True, extra="forbid"
    )
