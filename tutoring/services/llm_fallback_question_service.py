class LLMFallbackQuestionGenerationError(Exception):
    pass


class LLMFallbackQuestionService:
    def __init__(self, prompt_service, llm_service):
        self.prompt_service = prompt_service
        self.llm_service = llm_service

    def generate_question(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
    ) -> dict:
        prompt = self.prompt_service.build_prompt(
            subject_id=subject_id,
            topic_id=topic_id,
            target_difficulty=target_difficulty,
        )

        questions = self.llm_service.generate_from_prompt(
            prompt=prompt,
            expected_count=1,
        )

        if not questions:
            raise LLMFallbackQuestionGenerationError(
                "LLM did not return any fallback question."
            )

        question_data = questions[0]
        self._validate_question_data(question_data)

        return question_data

    def _validate_question_data(self, question_data: dict) -> None:
        required_fields = [
            "text",
            "type",
            "answers",
            "correctAnswers",
            "difficulty",
        ]

        for field in required_fields:
            if field not in question_data:
                raise LLMFallbackQuestionGenerationError(
                    f"Missing field from LLM response: {field}"
                )

        if question_data["type"] not in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
            raise LLMFallbackQuestionGenerationError(
                "Invalid question type from LLM."
            )

        answers = question_data["answers"]
        correct_answers = question_data["correctAnswers"]

        if not isinstance(answers, list) or len(answers) != 4:
            raise LLMFallbackQuestionGenerationError(
                "LLM question must contain exactly 4 answers."
            )

        if not isinstance(correct_answers, list) or len(correct_answers) < 1:
            raise LLMFallbackQuestionGenerationError(
                "LLM question must contain at least one correct answer."
            )

        for correct_answer in correct_answers:
            if correct_answer not in answers:
                raise LLMFallbackQuestionGenerationError(
                    "correctAnswers must contain only values from answers."
                )

        if question_data["type"] == "SINGLE_CHOICE" and len(correct_answers) != 1:
            raise LLMFallbackQuestionGenerationError(
                "SINGLE_CHOICE must have exactly one correct answer."
            )

        try:
            difficulty = float(question_data["difficulty"])
        except (TypeError, ValueError) as exc:
            raise LLMFallbackQuestionGenerationError(
                "Difficulty must be a valid float."
            ) from exc

        if difficulty < 0.0 or difficulty > 1.0:
            raise LLMFallbackQuestionGenerationError(
                "Difficulty must be between 0.0 and 1.0."
            )