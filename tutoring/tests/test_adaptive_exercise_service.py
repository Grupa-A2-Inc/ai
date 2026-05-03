from types import SimpleNamespace

from django.test import TestCase

from tutoring.models import Question, QuestionType, StudentProfile
from tutoring.services.adaptive_exercise_service import (
    AdaptiveExerciseService,
    StudentNotFoundError,
)


class AdaptiveExerciseServiceTests(TestCase):
    def test_generate_exercises_raises_when_student_does_not_exist(self):
        service = AdaptiveExerciseService()

        with self.assertRaises(StudentNotFoundError):
            service.generate_exercises(
                student_id="missing-student",
                subject_id=1,
                topic_id=101,
                count=1,
            )

    def test_generate_exercises_stops_when_recommendation_engine_returns_none(self):
        StudentProfile.objects.create(student_id="student-1", is_active=True)

        service = AdaptiveExerciseService()
        service.engine = SimpleNamespace(
            recommend=(
                lambda user_id,
                subject_id,
                topic_id,
                excluded_question_ids=None: None
            )
        )

        exercises = service.generate_exercises(
            student_id="student-1",
            subject_id=1,
            topic_id=101,
            count=3,
        )

        self.assertEqual(exercises, [])

    def test_generate_exercises_stops_when_recommendation_is_duplicate(self):
        StudentProfile.objects.create(student_id="student-1", is_active=True)
        question = Question.objects.create(
            subject_id=1,
            topic_id=101,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Question content",
        )
        recommendation = SimpleNamespace(question_id=question.id)

        class DuplicateRecommendationEngine:
            def __init__(self):
                self.calls = 0

            def recommend(
                self,
                user_id,
                subject_id,
                topic_id,
                excluded_question_ids=None,
            ):
                self.calls += 1
                return recommendation

        service = AdaptiveExerciseService()
        service.engine = DuplicateRecommendationEngine()
        service.serializer = SimpleNamespace(
            serialize=lambda question, exercise_id: {
                "exerciseId": exercise_id,
                "text": question.content,
            }
        )

        exercises = service.generate_exercises(
            student_id="student-1",
            subject_id=1,
            topic_id=101,
            count=2,
        )

        question.refresh_from_db()

        self.assertEqual(
            exercises,
            [
                {
                    "exerciseId": f"ai-{question.id}",
                    "text": "Question content",
                }
            ],
        )
        self.assertEqual(question.ml_exercise_id, f"ai-{question.id}")
        self.assertEqual(service.engine.calls, 2)

    def test_generate_exercises_passes_generated_questions_as_exclusions(self):
        StudentProfile.objects.create(student_id="student-1", is_active=True)
        question_one = Question.objects.create(
            subject_id=1,
            topic_id=101,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Question 1",
        )
        question_two = Question.objects.create(
            subject_id=1,
            topic_id=101,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Question 2",
        )

        class ExclusionAwareEngine:
            def recommend(
                self,
                user_id,
                subject_id,
                topic_id,
                excluded_question_ids=None,
            ):
                excluded_question_ids = set(excluded_question_ids or [])
                if question_one.id not in excluded_question_ids:
                    return SimpleNamespace(question_id=question_one.id)
                if question_two.id not in excluded_question_ids:
                    return SimpleNamespace(question_id=question_two.id)
                return None

        service = AdaptiveExerciseService()
        service.engine = ExclusionAwareEngine()
        service.serializer = SimpleNamespace(
            serialize=lambda question, exercise_id: {
                "exerciseId": exercise_id,
                "text": question.content,
            }
        )

        exercises = service.generate_exercises(
            student_id="student-1",
            subject_id=1,
            topic_id=101,
            count=2,
        )

        self.assertEqual(
            exercises,
            [
                {
                    "exerciseId": f"ai-{question_one.id}",
                    "text": "Question 1",
                },
                {
                    "exerciseId": f"ai-{question_two.id}",
                    "text": "Question 2",
                },
            ],
        )
