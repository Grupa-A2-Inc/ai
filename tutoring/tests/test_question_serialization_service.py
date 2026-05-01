from django.test import TestCase

from tutoring.models import (
    Question,
    QuestionCorrectOption,
    QuestionOption,
    QuestionType,
)
from tutoring.services.question_serialization_service import (
    QuestionSerializationService,
)


class QuestionSerializationServiceTests(TestCase):
    def test_serialize_question_orders_answers_and_maps_correct_answers(self):
        question = Question.objects.create(
            subject_id=1,
            topic_id=101,
            ml_exercise_id="exercise-1",
            question_type=QuestionType.MULTIPLE_CHOICE,
            content="Choose the prime numbers.",
            difficulty=0.75,
        )
        option_b = QuestionOption.objects.create(
            question=question,
            text="4",
            display_order=2,
        )
        option_a = QuestionOption.objects.create(
            question=question,
            text="2",
            display_order=1,
        )
        option_c = QuestionOption.objects.create(
            question=question,
            text="3",
            display_order=3,
        )
        QuestionCorrectOption.objects.create(question=question, option=option_a)
        QuestionCorrectOption.objects.create(question=question, option=option_c)

        payload = QuestionSerializationService().serialize(
            question=question,
            exercise_id="ai-1",
        )

        self.assertEqual(
            payload,
            {
                "exerciseId": "ai-1",
                "text": "Choose the prime numbers.",
                "type": "MULTIPLE_CHOICE",
                "answers": ["2", "4", "3"],
                "correctAnswers": ["2", "3"],
                "difficulty": 0.75,
            },
        )
        self.assertEqual(option_b.text, "4")

    def test_map_question_type_keeps_unknown_types_uppercase(self):
        service = QuestionSerializationService()

        self.assertEqual(
            service._map_question_type("single_choice"),
            "SINGLE_CHOICE",
        )
        self.assertEqual(
            service._map_question_type("multiple_choice"),
            "MULTIPLE_CHOICE",
        )
        self.assertEqual(service._map_question_type("free_text"), "FREE_TEXT")
