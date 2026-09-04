from pydantic import BaseModel


class ScoreBreakdownOut(BaseModel):
    total: int
    components: dict[str, float]
    weighted: dict[str, float]
    explanation: str


class RecommendationOut(BaseModel):
    dimension: str
    entity_label: str
    multiplier: float
    sample_size: int
    explanation: str
