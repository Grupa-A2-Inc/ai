
from tutoring.models import Question, StudentProfile
from tutoring.services.recommendation_engine import QuestionRecommendationEngine
from tutoring.services.question_serialization_service import QuestionSerializationService


class StudentNotFoundError(Exception):
    pass


class AdaptiveExerciseService:
    def __init__(self):
        self.engine = QuestionRecommendationEngine()
        self.serializer = QuestionSerializationService()

    def generate_exercises(
        self,
        student_id: str,
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
                break

            if recommendation.question_id in generated_question_ids:
                break

            generated_question_ids.add(recommendation.question_id)

            question = Question.objects.get(id=recommendation.question_id)

            exercise_id = self._build_exercise_id(question)

            question.ml_exercise_id = exercise_id
            question.save(update_fields=["ml_exercise_id"])

            exercises.append(
                self.serializer.serialize(
                    question=question,
                    exercise_id=exercise_id,
                )
            )

        return exercises

    def _validate_student_exists(self, student_id: str) -> None:
        exists = StudentProfile.objects.filter(
            student_id=student_id,
            is_active=True,
        ).exists()

        if not exists:
            raise StudentNotFoundError()

    def _build_exercise_id(self, question: Question) -> str:
        return f"ai-{question.id}"
