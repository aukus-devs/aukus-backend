from src.api.utils import ApiModel
from src.enums import RulesCategory


class RulesVersion(ApiModel):
    content: str
    category: RulesCategory
    created_at: int


class NewRulesVersionRequest(ApiModel):
    content: str
    category: RulesCategory


class RulesResponse(ApiModel):
    versions: list[RulesVersion]
