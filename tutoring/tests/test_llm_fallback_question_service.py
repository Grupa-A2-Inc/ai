from types import SimpleNamespace

from django.test import TestCase

from tutoring.models import QuestionType
from tutoring.services.fallback_question_prompt_service import (
    FallbackQuestionPromptService,
)
from tutoring.services.llm_fallback_question_service import LLMFallbackQuestionService


class FallbackQuestionPromptServiceTests(TestCase):
    def test_build_prompt_adds_subject_specific_calibration(self):
        prompt = FallbackQuestionPromptService().build_prompt(
            subject_id=2,
            topic_id=1102,
            target_difficulty=0.6,
            mastery_score=0.5,
        )

        self.assertIn("General difficulty calibration", prompt)
        self.assertIn("Subject-specific difficulty calibration for subjectId 2", prompt)
        self.assertIn("standard application with one or two expected steps", prompt)
        self.assertIn('"topicName": "Ecuații și inecuații"', prompt)
        self.assertIn('"targetDifficulty": 0.6', prompt)


class LLMFallbackQuestionServiceTests(TestCase):
    def test_generate_and_save_uses_target_difficulty_and_persists_question(self):
        generated_payload = {
            "text": "Cât este x dacă 2x = 6?",
            "type": "SINGLE_CHOICE",
            "answers": ["1", "2", "3", "4"],
            "correctAnswers": ["3"],
            "difficulty": 0.95,
        }

        class GenerationService:
            def generate_from_prompt(self, prompt, expected_count=None):
                return [generated_payload]

        context = SimpleNamespace(
            target_difficulty=0.6,
            mastery_score=0.5,
            ml_features={"attempt_count_on_topic": 3},
            seen_question_ids=set(),
            student_context=SimpleNamespace(
                candidate_questions=[],
                recent_history=[],
                history=[],
            ),
        )

        question = LLMFallbackQuestionService(
            generation_service=GenerationService()
        ).generate_and_save(
            subject_id=2,
            topic_id=1102,
            recommendation_context=context,
        )

        self.assertIsNotNone(question)
        self.assertEqual(question.subject_id, 2)
        self.assertEqual(question.topic_id, 1102)
        self.assertEqual(question.question_type, QuestionType.SINGLE_CHOICE)
        self.assertEqual(question.difficulty, 0.6)
        self.assertEqual(question.options.count(), 4)
        self.assertEqual(question.correct_options.count(), 1)
        self.assertEqual(question.ml_exercise_id, f"ai-{question.id}")
