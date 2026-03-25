class QuestionRecommendationResult:
    def __init__(self, question_id: int, difficulty: float, source: str):
        self.question_id = question_id
        self.difficulty = difficulty
        self.source = source