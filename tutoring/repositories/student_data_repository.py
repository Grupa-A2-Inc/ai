from tutoring.models import Question, StudentInteraction
from tutoring.dto.student_context import StudentContext


class StudentDataRepository:
    def get_student_history(self, user_id: int, subject_id: int, topic_id: int):
        return StudentInteraction.objects.filter(
            user_id=user_id,
            question__subject_id=subject_id,
            question__topic_id=topic_id,
        ).select_related("question").order_by("created_at")

    def get_recent_student_history(self, user_id: int, subject_id: int, topic_id: int, limit: int = 10):
        return StudentInteraction.objects.filter(
            user_id=user_id,
            question__subject_id=subject_id,
            question__topic_id=topic_id,
        ).select_related("question").order_by("-created_at")[:limit]

    def get_seen_question_ids(self, user_id: int, subject_id: int, topic_id: int):
        return list(
            StudentInteraction.objects.filter(
                user_id=user_id,
                question__subject_id=subject_id,
                question__topic_id=topic_id,
            ).values_list("question_id", flat=True).distinct()
        )

    def get_candidate_questions(self, subject_id: int, topic_id: int):
        return Question.objects.filter(
            subject_id=subject_id,
            topic_id=topic_id,
            is_active=True,
        )

    def build_student_context(self, user_id: int, subject_id: int, topic_id: int) -> StudentContext:
        return StudentContext(
            history=self.get_student_history(user_id, subject_id, topic_id),
            recent_history=self.get_recent_student_history(user_id, subject_id, topic_id),
            seen_question_ids=self.get_seen_question_ids(user_id, subject_id, topic_id),
            candidate_questions=self.get_candidate_questions(subject_id, topic_id),
        )
