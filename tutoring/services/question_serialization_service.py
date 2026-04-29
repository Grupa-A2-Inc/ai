class QuestionSerializationService:
    def serialize(self, question, exercise_id: str) -> dict:
        options = list(
            question.options.all().order_by("display_order")
        )

        correct_option_ids = set(
            question.correct_options.values_list("option_id", flat=True)
        )

        answers = [
            option.text for option in options
        ]

        correct_answers = [
            option.text for option in options
            if option.id in correct_option_ids
        ]

        question_type = self._map_question_type(question.question_type)

        return {
            "exerciseId": exercise_id,
            "text": question.content,
            "type": question_type,
            "answers": answers,
            "correctAnswers": correct_answers,
            "difficulty": question.difficulty,
        }

    def _map_question_type(self, question_type: str) -> str:
        if question_type == "single_choice":
            return "SINGLE_CHOICE"

        if question_type == "multiple_choice":
            return "MULTIPLE_CHOICE"

        return question_type.upper()