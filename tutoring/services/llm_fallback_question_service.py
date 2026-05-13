import logging

from django.conf import settings

from tutoring.services.fallback_question_persistence_service import (
    FallbackQuestionPersistenceService,
)
from tutoring.services.fallback_question_prompt_service import (
    FallbackQuestionPromptService,
)
from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationError,
    LLMQuestionGenerationService,
)

logger = logging.getLogger(__name__)


class LLMFallbackQuestionService:
    def __init__(
        self,
        prompt_service=None,
        generation_service=None,
        persistence_service=None,
    ):
        self.prompt_service = prompt_service or FallbackQuestionPromptService()
        fallback_provider = getattr(settings, "LLM_FALLBACK_PROVIDER", "ollama")
        self.generation_service = generation_service or LLMQuestionGenerationService(
            provider=fallback_provider
        )
        self.persistence_service = (
            persistence_service or FallbackQuestionPersistenceService()
        )

    def generate_and_save(
        self,
        subject_id: int,
        topic_id: int,
        recommendation_context,
    ):
        try:
            target_difficulty = recommendation_context.target_difficulty
            prompt = self.prompt_service.build_prompt(
                subject_id=subject_id,
                topic_id=topic_id,
                target_difficulty=target_difficulty,
                mastery_score=recommendation_context.mastery_score,
                student_features=recommendation_context.ml_features,
                example_questions=self._example_questions(
                    recommendation_context=recommendation_context,
                    target_difficulty=target_difficulty,
                ),
                avoid_question_texts=self._avoid_question_texts(
                    recommendation_context.student_context
                ),
            )
        except Exception:
            logger.exception("Fallback question prompt assembly failed")
            return None

        try:
            questions = self.generation_service.generate_from_prompt(
                prompt=prompt,
                expected_count=1,
                default_difficulty=target_difficulty,
            )
        except LLMQuestionGenerationError:
            logger.exception("LLM fallback question generation failed")
            return None
        except Exception:
            logger.exception("Unexpected fallback question generation error")
            return None

        if not questions:
            logger.error("LLM fallback returned no questions. Prompt: %s", prompt)
            return None

        question_payload = questions[0]
        if "difficulty" not in question_payload:
            question_payload["difficulty"] = target_difficulty

        calibrated_difficulty = self._clamp_to_target(
            question_payload.get("difficulty"),
            target_difficulty,
        )
        question_payload["difficulty"] = calibrated_difficulty

        try:
            return self.persistence_service.save_question(
                question_payload=question_payload,
                subject_id=subject_id,
                topic_id=topic_id,
                difficulty=calibrated_difficulty,
            )
        except Exception:
            logger.exception("Generated fallback question could not be saved")
            return None

    def _example_questions(
        self,
        recommendation_context,
        target_difficulty: float,
    ) -> list[dict]:
        seen_ids = set(recommendation_context.seen_question_ids or [])
        questions = [
            question
            for question in recommendation_context.student_context.candidate_questions
            if question.id not in seen_ids
        ]

        if not questions:
            questions = list(
                recommendation_context.student_context.candidate_questions
            )

        closest_questions = sorted(
            questions,
            key=lambda question: abs(question.difficulty - target_difficulty),
        )[:3]

        return [
            {
                "text": question.content,
                "difficulty": round(float(question.difficulty), 3),
            }
            for question in closest_questions
        ]

    def _avoid_question_texts(self, student_context) -> list[str]:
        recent_history = list(getattr(student_context, "recent_history", None) or [])
        if not recent_history:
            recent_history = list(getattr(student_context, "history", []) or [])[-5:]

        texts = []
        for interaction in recent_history:
            question = getattr(interaction, "question", None)
            content = getattr(question, "content", None)
            if content:
                texts.append(content)

        return texts[:5]

    def _clamp_to_target(
        self,
        generated_difficulty,
        target_difficulty: float,
    ) -> float:
        target = max(0.0, min(float(target_difficulty), 1.0))

        try:
            generated = float(generated_difficulty)
        except (TypeError, ValueError):
            return target

        if abs(generated - target) > 0.15:
            return target

        return max(0.0, min(generated, 1.0))
