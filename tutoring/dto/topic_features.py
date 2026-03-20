from dataclasses import dataclass

@dataclass
class TopicFeatures:
    mastery_score: float
    accuracy_ratio: float
    recent_test_accuracy: float
    recent_answer_accuracy: float
    avg_time_per_answer: float
    material_completion_ratio: float
    inactivity_days: int
    total_attempts: int
    correct_answers: int