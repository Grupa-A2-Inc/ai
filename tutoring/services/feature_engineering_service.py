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
        correct_count = sum(1 for interaction in history if interaction.is_correct)
        accuracy = correct_count / attempt_count

        avg_time = avg_time = sum(interaction.time_spent if interaction.is_correct else 60 for interaction in history) / attempt_count

        return TopicFeatures(
            accuracy=accuracy,
            avg_time=avg_time,
            attempt_count=attempt_count,
        )