from tutoring.dto.difficulty_result import DifficultyResult


class DifficultyEstimator:
    def estimate(self, mastery_score: float) -> DifficultyResult:
        mastery_score = max(0.0, min(mastery_score, 1.0))
        target = min(mastery_score + 0.1, 1.0)
        return DifficultyResult(target_difficulty=target)