from dataclasses import dataclass

@dataclass
class MasteryResult:
    user_id: int
    subject_id: int
    topic_id: int
    mastery_score: float
    confidence: float
    source: str