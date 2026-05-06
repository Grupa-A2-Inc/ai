from django.db import transaction

from tutoring.models import (
    Question,
    QuestionOption,
    QuestionCorrectOption,
    QuestionType,
)


class FallbackQuestionPersistenceService:
    @transaction.atomic
    def save_generated_question(
        self,
        subject_id: int,
        topic_id: int,
        question_data: dict,
    ) -> Question:
        question_type = self._map_question_type(question_data["type"])

        question = Question.objects.create(
            subject_id=subject_id,
            topic_id=topic_id,
            question_type=question_type,
            content=question_data["text"],
            difficulty=float(question_data["difficulty"]),
            is_active=True,
        )

        options_by_text = {}

        for index, answer_text in enumerate(question_data["answers"], start=1):
            option = QuestionOption.objects.create(
                question=question,
                text=answer_text,
                display_order=index,
            )
            options_by_text[answer_text] = option

        for correct_answer_text in question_data["correctAnswers"]:
            QuestionCorrectOption.objects.create(
                question=question,
                option=options_by_text[correct_answer_text],
            )

        return question

    def _map_question_type(self, llm_type: str) -> str:
        if llm_type == "SINGLE_CHOICE":
            return QuestionType.SINGLE_CHOICE

        if llm_type == "MULTIPLE_CHOICE":
            return QuestionType.MULTIPLE_CHOICE

        raise ValueError(f"Unsupported question type: {llm_type}")