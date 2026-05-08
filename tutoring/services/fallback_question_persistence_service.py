from django.db import transaction

from tutoring.models import Question, QuestionCorrectOption, QuestionOption, QuestionType


class FallbackQuestionPersistenceService:
    @transaction.atomic
    def save_question(
        self,
        question_payload: dict,
        subject_id: int,
        topic_id: int,
        difficulty: float,
    ) -> Question:
        question = Question.objects.create(
            subject_id=subject_id,
            topic_id=topic_id,
            question_type=self._map_question_type(question_payload["type"]),
            content=question_payload["text"],
            difficulty=max(0.0, min(float(difficulty), 1.0)),
            is_active=True,
        )

        option_by_text = {}
        for index, answer in enumerate(question_payload["answers"], start=1):
            option = QuestionOption.objects.create(
                question=question,
                text=answer,
                display_order=index,
            )
            option_by_text[answer] = option

        for correct_answer in question_payload["correctAnswers"]:
            if correct_answer not in option_by_text:
                raise ValueError(
                    "Correct answer is missing from generated answers: "
                    f"{correct_answer!r}. Payload: {question_payload!r}"
                )

            QuestionCorrectOption.objects.create(
                question=question,
                option=option_by_text[correct_answer],
            )

        question.ml_exercise_id = f"ai-{question.id}"
        question.save(update_fields=["ml_exercise_id"])

        return question

    def _map_question_type(self, question_type: str) -> str:
        if question_type == "SINGLE_CHOICE":
            return QuestionType.SINGLE_CHOICE

        if question_type == "MULTIPLE_CHOICE":
            return QuestionType.MULTIPLE_CHOICE

        raise ValueError(f"Unsupported question type: {question_type}")
