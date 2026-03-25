from tutoring.dto.recommandation_result import QuestionRecommendationResult

class QuestionRecommendationEngine:
    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        return QuestionRecommendationResult(
            question_id=1,
            difficulty=0.5,
            source="selection",
        )

'''
@Ionut
Cam asa ar trebuie sa arate mai tarziu -> Cine implementeaza sau modifica acest fisier lasati acest bloc de cod pls
Also sa il luati in considerare ce scrie aici ca la ceva de genul asta ma gandesc ca va arata engine-ul, for now am facut asa ca 
sa testez API-ul pentru Sprint 1

from tutoring.repositories.student_data_repository import StudentDataRepository
from tutoring.services.feature_engineering_service import FeatureEngineeringService
from tutoring.services.mastery_estimator import MasteryEstimator
from tutoring.services.difficulty_estimator import DifficultyEstimator
from tutoring.services.question_selection_engine import QuestionSelectionEngine
from tutoring.dto.question_recommendation_result import QuestionRecommendationResult


class QuestionRecommendationEngine:
    def __init__(self):
        self.repository = StudentDataRepository()
        self.feature_service = FeatureEngineeringService()
        self.mastery_estimator = MasteryEstimator()
        self.difficulty_estimator = DifficultyEstimator()
        self.selection_engine = QuestionSelectionEngine()

    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        features = self.feature_service.build_features(student_context)
        mastery_result = self.mastery_estimator.estimate(features)
        difficulty_result = self.difficulty_estimator.estimate(mastery_result.mastery_score)

        selected_question = self.selection_engine.select(
            candidate_questions=student_context.candidate_questions,
            target_difficulty=difficulty_result.target_difficulty,
            seen_question_ids=student_context.seen_question_ids,
        )

        if selected_question is None:
            return None

        return QuestionRecommendationResult(
            question_id=selected_question.id,
            difficulty=selected_question.difficulty_initial,
            source="selection",
        )
'''
