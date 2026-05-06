import csv
from pathlib import Path

from tutoring.models import StudentInteraction, StudentProfile, StudentTopicLevel


class StudentMasteryDatasetBuilder:
    MAX_TIME = 120.0

    def build_dataset(self, output_path: str) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows = self._build_rows()

        with output_file.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=self._fieldnames(),
            )

            writer.writeheader()
            writer.writerows(rows)

    def _build_rows(self) -> list[dict]:
        interactions = StudentInteraction.objects.select_related(
            "question"
        ).order_by(
            "user_id",
            "question__subject_id",
            "question__topic_id",
            "created_at",
        )

        grouped_history = {}
        rows = []

        for interaction in interactions:
            subject_id = interaction.question.subject_id
            topic_id = interaction.question.topic_id

            key = (
                interaction.user_id,
                subject_id,
                topic_id,
            )

            previous_history = grouped_history.get(key, [])

            features = self._build_features(
                interaction=interaction,
                previous_history=previous_history,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            rows.append(features)

            previous_history.append(interaction)
            grouped_history[key] = previous_history

        return rows

    def _build_features(
        self,
        interaction,
        previous_history,
        subject_id: int,
        topic_id: int,
    ) -> dict:
        attempt_count = len(previous_history)

        previous_scores = [
            item.score for item in previous_history
        ]

        previous_times = [
            item.time_spent for item in previous_history
        ]

        average_score = (
            sum(previous_scores) / len(previous_scores)
            if previous_scores else 0.5
        )

        average_time = (
            sum(previous_times) / len(previous_times)
            if previous_times else 60.0
        )

        recent_history = previous_history[-5:]

        recent_scores = [
            item.score for item in recent_history
        ]

        recent_times = [
            item.time_spent for item in recent_history
        ]

        recent_average_score = (
            sum(recent_scores) / len(recent_scores)
            if recent_scores else average_score
        )

        recent_average_time = (
            sum(recent_times) / len(recent_times)
            if recent_times else average_time
        )

        normalized_time = min(interaction.time_spent / self.MAX_TIME, 1.0)
        normalized_average_time = min(average_time / self.MAX_TIME, 1.0)
        normalized_recent_time = min(recent_average_time / self.MAX_TIME, 1.0)

        current_mastery = self._get_current_mastery(
            student_id=interaction.user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        target_mastery = self._calculate_target_mastery(
            current_mastery=current_mastery,
            average_score=average_score,
            normalized_average_time=normalized_average_time,
        )

        return {
            "student_id": interaction.user_id,
            "subject_id": subject_id,
            "topic_id": topic_id,
            "question_id": interaction.question_id,
            "question_difficulty": interaction.question.difficulty,
            "score": interaction.score,
            "is_correct": 1 if interaction.is_correct else 0,
            "time_spent": interaction.time_spent,
            "normalized_time": normalized_time,
            "attempt_count_on_topic": attempt_count,
            "average_score_on_topic": average_score,
            "average_time_on_topic": average_time,
            "normalized_average_time": normalized_average_time,
            "recent_average_score": recent_average_score,
            "recent_average_time": recent_average_time,
            "normalized_recent_time": normalized_recent_time,
            "current_mastery": current_mastery,
            "target_mastery": target_mastery,
        }

    def _get_current_mastery(
        self,
        student_id: str,
        subject_id: int,
        topic_id: int,
    ) -> float:
        try:
            student = StudentProfile.objects.get(
                student_id=student_id,
                is_active=True,
            )

            topic_level = StudentTopicLevel.objects.get(
                student=student,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            return topic_level.mastery_score

        except (StudentProfile.DoesNotExist, StudentTopicLevel.DoesNotExist):
            return 0.5

    def _calculate_target_mastery(
        self,
        current_mastery: float,
        average_score: float,
        normalized_average_time: float,
    ) -> float:
        performance_mastery = (
            0.7 * average_score
            + 0.3 * (1 - normalized_average_time)
        )

        target_mastery = (
            0.8 * current_mastery
            + 0.2 * performance_mastery
        )

        return max(0.0, min(target_mastery, 1.0))

    def _fieldnames(self) -> list[str]:
        return [
            "student_id",
            "subject_id",
            "topic_id",
            "question_id",
            "question_difficulty",
            "score",
            "is_correct",
            "time_spent",
            "normalized_time",
            "attempt_count_on_topic",
            "average_score_on_topic",
            "average_time_on_topic",
            "normalized_average_time",
            "recent_average_score",
            "recent_average_time",
            "normalized_recent_time",
            "current_mastery",
            "target_mastery",
        ]