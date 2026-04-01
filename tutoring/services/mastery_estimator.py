from tutoring.dto.mastery_result import MasteryResult


class MasteryEstimator:
    def estimate(self, normalized_features) -> MasteryResult:
        mastery = (
            0.7 * normalized_features.accuracy
            + 0.3 * (1 - normalized_features.avg_time)
        )

        mastery = max(0.0, min(mastery, 1.0))

        return MasteryResult(mastery_score=mastery)