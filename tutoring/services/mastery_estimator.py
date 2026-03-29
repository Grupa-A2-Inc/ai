from tutoring.dto.mastery_result import MasteryResult

class MasteryEstimator:
    def estimate(self, features) -> MasteryResult:
        normalized_time = min(features.avg_time / 60.0, 1.0)

        mastery = 0.7 * features.accuracy + 0.3 * (1 - normalized_time)

        mastery = max(0.0, min(mastery, 1.0))

        return MasteryResult(mastery_score=mastery)
