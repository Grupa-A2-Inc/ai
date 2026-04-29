from django.db import transaction

from tutoring.models import (
    StudentProfile,
    StudentTopicLevel,
    StudentInteraction,
    Question,
)


class StudentNotFoundError(Exception):
    pass


class QuestionNotFoundError(Exception):
    pass


class FeedbackService:
    DEFAULT_MASTERY = 0.5
    OLD_MASTERY_WEIGHT = 0.8
    NEW_SCORE_WEIGHT = 0.2

    def record_feedback(self, student_id: str, subject_id: int, topic_id: int, results: list[dict]) -> None:
        student = self._get_student_or_raise(student_id)

        with transaction.atomic():
            self._save_student_interactions(student_id, subject_id, topic_id, results)
            self._update_student_topic_level(student, subject_id, topic_id, results)

    def _get_student_or_raise(self, student_id: str) -> StudentProfile:
        try:
            return StudentProfile.objects.get(
                student_id=student_id,
                is_active=True,
            )
        except StudentProfile.DoesNotExist as exc:
            raise StudentNotFoundError() from exc

    def _save_student_interactions(self, student_id: str, subject_id: int, topic_id: int, results: list[dict]) -> None:
        for result in results:
            ml_exercise_id = str(result["mlExerciseId"])
            score = float(result["score"])
            time_spent = float(result["timeSpent"])

            question = self._get_question_or_raise(
                ml_exercise_id=ml_exercise_id,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            StudentInteraction.objects.create(
                user_id=student_id,
                question=question,
                ml_exercise_id=ml_exercise_id,
                is_correct=self._is_correct(score),
                score=score,
                time_spent=time_spent,
            )

            self._update_question_statistics(question, score, time_spent)

    def _get_question_or_raise(self, ml_exercise_id: str, subject_id: int, topic_id: int) -> Question:
        try:
            return Question.objects.get(
                ml_exercise_id=ml_exercise_id,
                subject_id=subject_id,
                topic_id=topic_id,
                is_active=True,
            )
        except Question.DoesNotExist as exc:
            raise QuestionNotFoundError() from exc

    def _update_question_statistics(self, question: Question, score: float, time_spent: float) -> None:
        old_times_answered = question.times_answered
        old_avg_time_spent = question.avg_time_spent
        new_times_answered = old_times_answered + 1

        question.times_answered = new_times_answered

        if self._is_correct(score):
            question.times_correct += 1

        question.avg_time_spent = (
            (old_avg_time_spent * old_times_answered + time_spent)
            / new_times_answered
        )

        question.save(
            update_fields=[
                "times_answered",
                "times_correct",
                "avg_time_spent",
            ]
        )

    def _update_student_topic_level(self, student: StudentProfile, subject_id: int, topic_id: int, results: list[dict]) -> None:
        topic_level, _ = StudentTopicLevel.objects.get_or_create(
            student=student,
            subject_id=subject_id,
            topic_id=topic_id,
            defaults={"mastery_score": self.DEFAULT_MASTERY},
        )

        average_score = self._calculate_average_score(results)

        topic_level.mastery_score = self._clamp(
            self.OLD_MASTERY_WEIGHT * topic_level.mastery_score
            + self.NEW_SCORE_WEIGHT * average_score
        )
        topic_level.save(update_fields=["mastery_score"])

    def _calculate_average_score(self, results: list[dict]) -> float:
        return sum(float(result["score"]) for result in results) / len(results)

    def _is_correct(self, score: float) -> bool:
        return score == 1.0

    def _clamp(self, value: float) -> float:
        return max(0.0, min(value, 1.0))