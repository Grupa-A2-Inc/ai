from django.test import TestCase

from tutoring.models import (
    StudentProfile,
    Question,
    QuestionOption,
    QuestionCorrectOption,
)
from tutoring.services.adaptive_exercise_service import (
    AdaptiveExerciseService,
    AdaptiveExerciseServiceUnavailableError,
)


class AdaptiveExerciseFallbackTests(TestCase):
    def setUp(self):
        StudentProfile.objects.create(
            student_id=1,
            is_active=True,
        )

    def test_fallback_creates_question_when_engine_returns_none(self):
        service = AdaptiveExerciseService()

        service.engine.recommend = lambda *args, **kwargs: None

        service.fallback_generator.generate_question = lambda *args, **kwargs: {
            "text": "Generated fallback question",
            "type": "SINGLE_CHOICE",
            "answers": ["A", "B", "C", "D"],
            "correctAnswers": ["A"],
            "difficulty": 0.5,
        }

        exercises = service.generate_exercises(
            student_id=1,
            subject_id=2,
            topic_id=1102,
            count=1,
        )

        self.assertEqual(len(exercises), 1)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionOption.objects.count(), 4)
        self.assertEqual(QuestionCorrectOption.objects.count(), 1)

        question = Question.objects.first()

        self.assertIsNotNone(question.ml_exercise_id)
        self.assertEqual(question.content, "Generated fallback question")
        self.assertEqual(exercises[0]["text"], "Generated fallback question")
        self.assertEqual(exercises[0]["exerciseId"], question.ml_exercise_id)

    def test_engine_finds_question_without_calling_fallback(self):
        question = Question.objects.create(
            subject_id=2,
            topic_id=1102,
            question_type="single_choice",
            content="Existing question",
            difficulty=0.5,
            is_active=True,
        )

        option_a = QuestionOption.objects.create(
            question=question,
            text="A",
            display_order=1,
        )
        QuestionOption.objects.create(question=question, text="B", display_order=2)
        QuestionOption.objects.create(question=question, text="C", display_order=3)
        QuestionOption.objects.create(question=question, text="D", display_order=4)

        QuestionCorrectOption.objects.create(
            question=question,
            option=option_a,
        )

        class Recommendation:
            question_id = question.id
            difficulty = question.difficulty
            source = "test"

        service = AdaptiveExerciseService()
        service.engine.recommend = lambda *args, **kwargs: Recommendation()

        def fail_if_called(*args, **kwargs):
            raise AssertionError("Fallback should not be called")

        service.fallback_generator.generate_question = fail_if_called

        exercises = service.generate_exercises(
            student_id=1,
            subject_id=2,
            topic_id=1102,
            count=1,
        )

        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0]["text"], "Existing question")

    def test_llm_failure_raises_controlled_error(self):
        service = AdaptiveExerciseService()
        service.engine.recommend = lambda *args, **kwargs: None

        def failing_generator(*args, **kwargs):
            raise RuntimeError("LLM failed")

        service.fallback_generator.generate_question = failing_generator

        with self.assertRaises(AdaptiveExerciseServiceUnavailableError):
            service.generate_exercises(
                student_id=1,
                subject_id=2,
                topic_id=1102,
                count=1,
            )