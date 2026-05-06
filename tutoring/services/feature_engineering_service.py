from tutoring.dto.topic_features import TopicFeatures

class FeatureEngineeringService:
    MAX_TIME = 120.0

    def build_features(self, student_context) -> TopicFeatures:
        history = list(student_context.history)

        if not history:
            return TopicFeatures(
                accuracy=getattr(student_context, "topic_mastery_score", 0.5),
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

    def build_ml_features(
        self,
        student_context,
        subject_id: int,
        topic_id: int,
    ) -> dict:
        history = list(student_context.history)
        recent_history = list(
            getattr(student_context, "recent_history", None) or []
        )

        if not recent_history:
            recent_history = history[-5:]

        latest_interaction = history[-1] if history else None
        attempt_count = len(history)

        scores = [
            self._score_for_interaction(interaction)
            for interaction in history
        ]
        times = [
            self._time_for_interaction(interaction)
            for interaction in history
        ]

        average_score = (
            sum(scores) / len(scores)
            if scores else getattr(student_context, "topic_mastery_score", 0.5)
        )
        average_time = (
            sum(times) / len(times)
            if times else 60.0
        )

        recent_scores = [
            self._score_for_interaction(interaction)
            for interaction in recent_history
        ]
        recent_times = [
            self._time_for_interaction(interaction)
            for interaction in recent_history
        ]

        recent_average_score = (
            sum(recent_scores) / len(recent_scores)
            if recent_scores else average_score
        )
        recent_average_time = (
            sum(recent_times) / len(recent_times)
            if recent_times else average_time
        )

        latest_score = (
            self._score_for_interaction(latest_interaction)
            if latest_interaction is not None else average_score
        )
        latest_time = (
            self._time_for_interaction(latest_interaction)
            if latest_interaction is not None else average_time
        )

        return {
            "subject_id": subject_id,
            "topic_id": topic_id,
            "question_difficulty": self._question_difficulty(latest_interaction),
            "score": latest_score,
            "is_correct": 1 if self._is_correct(latest_interaction) else 0,
            "time_spent": latest_time,
            "normalized_time": self._normalize_time(latest_time),
            "attempt_count_on_topic": attempt_count,
            "average_score_on_topic": average_score,
            "average_time_on_topic": average_time,
            "normalized_average_time": self._normalize_time(average_time),
            "recent_average_score": recent_average_score,
            "recent_average_time": recent_average_time,
            "normalized_recent_time": self._normalize_time(recent_average_time),
            "current_mastery": getattr(student_context, "topic_mastery_score", 0.5),
        }

    def _score_for_interaction(self, interaction) -> float:
        if interaction is None:
            return 0.5
        if hasattr(interaction, "score"):
            return float(interaction.score)
        return 1.0 if getattr(interaction, "is_correct", False) else 0.0

    def _time_for_interaction(self, interaction) -> float:
        if interaction is None:
            return 60.0
        return float(getattr(interaction, "time_spent", 60.0))

    def _is_correct(self, interaction) -> bool:
        if interaction is None:
            return False
        return bool(getattr(interaction, "is_correct", False))

    def _question_difficulty(self, interaction) -> float:
        if interaction is None:
            return 0.5
        question = getattr(interaction, "question", None)
        return float(getattr(question, "difficulty", 0.5))

    def _normalize_time(self, time_spent: float) -> float:
        return min(float(time_spent) / self.MAX_TIME, 1.0)
