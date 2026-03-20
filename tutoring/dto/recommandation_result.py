from dataclasses import dataclass

@dataclass
class RecommendationResult:
    recommendation_type: str
    target_id: int | None
    target_type: str | None
    reason: str
    score: float