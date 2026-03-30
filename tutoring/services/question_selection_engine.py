class QuestionSelectionEngine:
    def select(self, candidate_questions, target_difficulty: float, seen_question_ids=None):
        seen_question_ids = set(seen_question_ids or [])

        eligible_questions = [
            question for question in candidate_questions
            if question.id not in seen_question_ids
        ]

        if not eligible_questions:
            return None

        return min(
            eligible_questions,
            key=lambda question: (
                abs(question.difficulty - target_difficulty),
                -question.difficulty
            )
        )