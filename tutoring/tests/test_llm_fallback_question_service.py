from types import SimpleNamespace

from django.test import TestCase, override_settings

from tutoring.models import Question, QuestionType
from tutoring.services.fallback_question_persistence_service import (
    FallbackQuestionPersistenceService,
)
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
    @override_settings(LLM_PROVIDER="gemini", LLM_FALLBACK_PROVIDER="ollama")
    def test_default_generation_service_uses_fallback_provider(self):
        service = LLMFallbackQuestionService()

        self.assertEqual(service.generation_service.provider, "ollama")

    def test_generate_and_save_uses_target_difficulty_and_persists_question(self):
        generated_payload = {
            "text": "Cât este x dacă 2x = 6?",
            "type": "SINGLE_CHOICE",
            "answers": ["1", "2", "3", "4"],
            "correctAnswers": ["3"],
            "difficulty": 0.7,
        }

        class GenerationService:
            def generate_from_prompt(
                self,
                prompt,
                expected_count=None,
                default_difficulty=None,
            ):
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
        self.assertEqual(question.difficulty, 0.7)
        self.assertEqual(question.options.count(), 4)
        self.assertEqual(question.correct_options.count(), 1)
        self.assertEqual(question.ml_exercise_id, f"ai-{question.id}")

    def test_generate_and_save_passes_target_difficulty_as_default(self):
        captured = {}
        generated_payload = {
            "text": "Cât este x dacă 2x = 6?",
            "type": "SINGLE_CHOICE",
            "answers": ["1", "2", "3", "4"],
            "correctAnswers": ["3"],
        }

        class GenerationService:
            def generate_from_prompt(
                self,
                prompt,
                expected_count=None,
                default_difficulty=None,
            ):
                captured["default_difficulty"] = default_difficulty
                generated_payload["difficulty"] = default_difficulty
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
        self.assertEqual(captured["default_difficulty"], 0.6)
        self.assertEqual(question.difficulty, 0.6)

    def test_generate_and_save_many_requests_and_persists_multiple_questions(self):
        captured = {}
        generated_payloads = [
            {
                "text": "Cât este x dacă 2x = 6?",
                "type": "SINGLE_CHOICE",
                "answers": ["1", "2", "3", "4"],
                "correctAnswers": ["3"],
                "difficulty": 0.6,
            },
            {
                "text": "Cât este x dacă x + 2 = 5?",
                "type": "SINGLE_CHOICE",
                "answers": ["1", "2", "3", "4"],
                "correctAnswers": ["3"],
                "difficulty": 0.6,
            },
        ]

        class GenerationService:
            def generate_from_prompt(
                self,
                prompt,
                expected_count=None,
                default_difficulty=None,
            ):
                captured["prompt"] = prompt
                captured["expected_count"] = expected_count
                return generated_payloads

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

        questions = LLMFallbackQuestionService(
            generation_service=GenerationService()
        ).generate_and_save_many(
            subject_id=2,
            topic_id=1102,
            recommendation_context=context,
            count=2,
        )

        self.assertEqual(len(questions), 2)
        self.assertEqual(captured["expected_count"], 2)
        self.assertIn("Generate exactly 2 question(s)", captured["prompt"])
        self.assertEqual(Question.objects.count(), 2)

    def test_generate_and_save_returns_none_when_prompt_context_is_invalid(self):
        service = LLMFallbackQuestionService()

        question = service.generate_and_save(
            subject_id=2,
            topic_id=1102,
            recommendation_context=SimpleNamespace(),
        )

        self.assertIsNone(question)
        self.assertEqual(Question.objects.count(), 0)

    def test_generate_and_save_returns_none_when_llm_returns_no_questions(self):
        class GenerationService:
            def generate_from_prompt(
                self,
                prompt,
                expected_count=None,
                default_difficulty=None,
            ):
                return []

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

        self.assertIsNone(question)
        self.assertEqual(Question.objects.count(), 0)

    def test_example_questions_treats_none_seen_ids_as_empty(self):
        question = SimpleNamespace(
            id=1,
            content="Existing question",
            difficulty=0.55,
        )
        context = SimpleNamespace(
            seen_question_ids=None,
            student_context=SimpleNamespace(candidate_questions=[question]),
        )

        examples = LLMFallbackQuestionService()._example_questions(
            recommendation_context=context,
            target_difficulty=0.6,
        )

        self.assertEqual(
            examples,
            [{"text": "Existing question", "difficulty": 0.55}],
        )


class FallbackQuestionPersistenceServiceTests(TestCase):
    def test_save_question_rejects_correct_answer_missing_from_answers(self):
        payload = {
            "text": "Cât este x dacă 2x = 6?",
            "type": "SINGLE_CHOICE",
            "answers": ["1", "2", "3", "4"],
            "correctAnswers": ["5"],
            "difficulty": 0.6,
        }

        with self.assertRaisesRegex(
            ValueError,
            "Correct answer is missing from generated answers: '5'",
        ):
            FallbackQuestionPersistenceService().save_question(
                question_payload=payload,
                subject_id=2,
                topic_id=1102,
                difficulty=0.6,
            )

        self.assertEqual(Question.objects.count(), 0)
