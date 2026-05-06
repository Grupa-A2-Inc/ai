import uuid

from tutoring.models import Question, StudentProfile
from tutoring.services.recommendation_engine import QuestionRecommendationEngine
from tutoring.services.question_serialization_service import QuestionSerializationService
from tutoring.services.fallback_question_prompt_service import (
    FallbackQuestionPromptService,
)
from tutoring.services.llm_fallback_question_service import (
    LLMFallbackQuestionService,
)
from tutoring.services.fallback_question_persistence_service import (
    FallbackQuestionPersistenceService,
)
from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationService,
)


class StudentNotFoundError(Exception):
    pass


class AdaptiveExerciseServiceUnavailableError(Exception):
    pass


class AdaptiveExerciseService:
    DEFAULT_FALLBACK_DIFFICULTY = 0.5

    def __init__(self):
        self.engine = QuestionRecommendationEngine()
        self.serializer = QuestionSerializationService()

        self.fallback_prompt_service = FallbackQuestionPromptService()
        self.llm_service = LLMQuestionGenerationService()
        self.fallback_generator = LLMFallbackQuestionService(
            prompt_service=self.fallback_prompt_service,
            llm_service=self.llm_service,
        )
        self.fallback_persistence = FallbackQuestionPersistenceService()

    def generate_exercises(
        self,
        student_id: int,
        subject_id: int,
        topic_id: int,
        count: int = 5,
    ) -> list[dict]:
        self._validate_student_exists(student_id)

        generated_question_ids = set()
        exercises = []

        max_attempts = count * 3
        attempts = 0

        while len(exercises) < count and attempts < max_attempts:
            attempts += 1

            recommendation = self.engine.recommend(
                user_id=student_id,
                subject_id=subject_id,
                topic_id=topic_id,
                excluded_question_ids=generated_question_ids,
            )

            if recommendation is None:
                fallback_question = self._create_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=self.DEFAULT_FALLBACK_DIFFICULTY,
                )

                exercises.append(
                    self._prepare_question_for_response(fallback_question)
                )
                continue

            if recommendation.question_id in generated_question_ids:
                fallback_question = self._create_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=recommendation.difficulty,
                )

                exercises.append(
                    self._prepare_question_for_response(fallback_question)
                )
                continue

            generated_question_ids.add(recommendation.question_id)

            question = Question.objects.get(
                id=recommendation.question_id,
                is_active=True,
            )

            exercises.append(
                self._prepare_question_for_response(question)
            )

        if not exercises:
            raise AdaptiveExerciseServiceUnavailableError()

        return exercises

    def _validate_student_exists(self, student_id: int) -> None:
        exists = StudentProfile.objects.filter(
            student_id=student_id,
            is_active=True,
        ).exists()

        if not exists:
            raise StudentNotFoundError()

    def _create_fallback_question(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
    ) -> Question:
        try:
            question_data = self.fallback_generator.generate_question(
                subject_id=subject_id,
                topic_id=topic_id,
                target_difficulty=target_difficulty,
            )

            return self.fallback_persistence.save_generated_question(
                subject_id=subject_id,
                topic_id=topic_id,
                question_data=question_data,
            )

        except Exception as exc:
            raise AdaptiveExerciseServiceUnavailableError() from exc

    def _prepare_question_for_response(self, question: Question) -> dict:
        exercise_id = f"ai-{question.id}-{uuid.uuid4().hex[:8]}"

        question.ml_exercise_id = exercise_id
        question.save(update_fields=["ml_exercise_id"])

        return self.serializer.serialize(
            question=question,
            exercise_id=exercise_id,
        )