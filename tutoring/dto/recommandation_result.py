class QuestionRecommendationResult:
    def __init__(self, question_id: int, subject_id: int, topic_id: int, difficulty: float, source: str):
        self.question_id = question_id
        self.subject_id = subject_id
        self.topic_id = topic_id
        self.difficulty = difficulty
        self.source = source