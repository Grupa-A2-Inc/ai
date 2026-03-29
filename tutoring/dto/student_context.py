class StudentContext:
    def __init__(self, history, recent_history, seen_question_ids, candidate_questions):
        self.history = history
        self.recent_history = recent_history
        self.seen_question_ids = seen_question_ids
        self.candidate_questions = candidate_questions
