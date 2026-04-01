from tutoring.dto.topic_features import TopicFeatures

class FeatureEngineeringService:
    def build_features(self, student_context) -> TopicFeatures:
        history = list(student_context.history)

        if not history:
            return TopicFeatures(
                accuracy=0.5,
                avg_time=30.0,
                attempt_count=0,
            )

        attempt_count = len(history)

        correct_count = sum(
            1 for interaction in history if interaction.is_correct
        )

        accuracy = correct_count / attempt_count

        avg_time = sum(
            interaction.time_spent for interaction in history
        ) / attempt_count

        return TopicFeatures(
            accuracy=accuracy,
            avg_time=avg_time,
            attempt_count=attempt_count,
        )

    def normalize(self, raw_features)-> TopicFeatures:
        return TopicFeatures(
            accuracy=raw_features.accuracy,
            avg_time=min(raw_features.avg_time / 60.0, 1.0),
            attempt_count=raw_features.attempt_count,
        )
