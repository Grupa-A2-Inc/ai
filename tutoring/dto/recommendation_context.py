from dataclasses import dataclass


@dataclass
class RecommendationContext:
    student_context: object
    mastery_score: float
    target_difficulty: float
    seen_question_ids: set
    normalized_features: object
    ml_features: dict
    strategy: str
