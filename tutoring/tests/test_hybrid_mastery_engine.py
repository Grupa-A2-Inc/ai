from unittest.mock import patch, MagicMock
from django.test import TestCase

from tutoring.services.recommendation_engine import QuestionRecommendationEngine


class HybridMasteryEngineTests(TestCase):

    def setUp(self):
        self.engine = QuestionRecommendationEngine()

        # 🔥 FIX GLOBAL: selection engine trebuie să returneze mereu o întrebare
        self.engine.selection_engine.select = MagicMock(return_value=MagicMock(
            id=1,
            subject_id=2,
            topic_id=1102,
            difficulty=0.5
        ))

    @patch("tutoring.services.recommendation_engine.StudentDataRepository")
    def test_rule_based_used_for_low_interactions(self, mock_repository):

        mock_context = MagicMock()
        mock_context.seen_question_ids = []
        mock_context.candidate_questions = [
            MagicMock(id=1, subject_id=2, topic_id=1102, difficulty=0.5)
        ]
        mock_repository.return_value.build_student_context.return_value = mock_context

        with patch.object(self.engine.feature_service, "build_features", return_value={
            "attempt_count_on_topic": 5
        }), patch.object(self.engine.feature_service, "normalize", return_value={
            "attempt_count_on_topic": 5
        }), patch.object(self.engine.rule_based_mastery_estimator, "estimate") as rule_mock:

            rule_mock.return_value = MagicMock(mastery_score=0.5)

            result = self.engine.recommend(1, 2, 1102)

            assert result is not None
            rule_mock.assert_called_once()

    @patch("tutoring.services.recommendation_engine.StudentDataRepository")
    def test_ml_used_for_high_interactions(self, mock_repository):

        mock_context = MagicMock()
        mock_context.seen_question_ids = []
        mock_context.candidate_questions = [
            MagicMock(id=1, subject_id=2, topic_id=1102, difficulty=0.5)
        ]
        mock_repository.return_value.build_student_context.return_value = mock_context

        features = {
            "attempt_count_on_topic": 15,
            "subject_id": 2,
            "topic_id": 1102,
            "question_difficulty": 0.5,
            "score": 1.0,
            "is_correct": 1,
            "time_spent": 40,
            "normalized_time": 0.3,
            "average_score_on_topic": 0.7,
            "average_time_on_topic": 50,
            "normalized_average_time": 0.4,
            "recent_average_score": 0.7,
            "recent_average_time": 50,
            "normalized_recent_time": 0.4,
            "current_mastery": 0.6,
        }

        with patch.object(self.engine.feature_service, "build_features", return_value=features), \
             patch.object(self.engine.feature_service, "normalize", return_value=features), \
             patch.object(self.engine.strategy_selector, "select", return_value="ml"), \
             patch.object(self.engine.ml_mastery_estimator, "estimate") as ml_mock:

            ml_mock.return_value = MagicMock(mastery_score=0.8)

            result = self.engine.recommend(1, 2, 1102)

            assert result is not None
            ml_mock.assert_called_once()

    @patch("tutoring.services.recommendation_engine.StudentDataRepository")
    def test_fallback_to_rule_based_if_ml_fails(self, mock_repository):

        mock_context = MagicMock()
        mock_context.seen_question_ids = []
        mock_context.candidate_questions = [
            MagicMock(id=1, subject_id=2, topic_id=1102, difficulty=0.5)
        ]
        mock_repository.return_value.build_student_context.return_value = mock_context

        features = {"attempt_count_on_topic": 15}

        with patch.object(self.engine.feature_service, "build_features", return_value=features), \
             patch.object(self.engine.feature_service, "normalize", return_value=features), \
             patch.object(self.engine.strategy_selector, "select", return_value="ml"), \
             patch.object(self.engine.ml_mastery_estimator, "estimate", side_effect=Exception("ML crash")), \
             patch.object(self.engine.rule_based_mastery_estimator, "estimate") as rule_mock:

            rule_mock.return_value = MagicMock(mastery_score=0.4)

            result = self.engine.recommend(1, 2, 1102)

            assert result is not None
            rule_mock.assert_called_once()