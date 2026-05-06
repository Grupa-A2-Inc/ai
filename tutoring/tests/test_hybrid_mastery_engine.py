from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import TestCase

from tutoring.dto.mastery_result import MasteryResult
from tutoring.services.recommendation_engine import QuestionRecommendationEngine


class FakeRepository:
    def __init__(self, student_context):
        self.student_context = student_context

    def build_student_context(self, user_id: int, subject_id: int, topic_id: int):
        return self.student_context


class HybridMasteryEngineTests(TestCase):
    def _build_engine(self, history):
        engine = QuestionRecommendationEngine()
        engine.repository = FakeRepository(
            SimpleNamespace(
                history=history,
                recent_history=history[-5:],
                seen_question_ids=[],
                candidate_questions=[
                    SimpleNamespace(
                        id=1,
                        subject_id=2,
                        topic_id=1102,
                        difficulty=0.5,
                    )
                ],
                topic_mastery_score=0.6,
            )
        )
        return engine

    def _interaction(self, score=1.0, time_spent=40.0, difficulty=0.5):
        return SimpleNamespace(
            is_correct=score == 1.0,
            score=score,
            time_spent=time_spent,
            question=SimpleNamespace(difficulty=difficulty),
        )

    def test_rule_based_used_for_low_interactions(self):
        engine = self._build_engine(
            [self._interaction() for _ in range(5)]
        )
        engine.rule_based_mastery_estimator.estimate = MagicMock(
            return_value=MasteryResult(mastery_score=0.5)
        )
        engine.strategy_selector.model_path = Path("missing-model.pkl")
        engine.ml_mastery_estimator.estimate = MagicMock()

        result = engine.recommend(1, 2, 1102)

        self.assertIsNotNone(result)
        engine.rule_based_mastery_estimator.estimate.assert_called_once()
        engine.ml_mastery_estimator.estimate.assert_not_called()

    def test_rule_based_used_for_high_interactions_when_model_is_missing(self):
        engine = self._build_engine(
            [self._interaction() for _ in range(10)]
        )
        engine.rule_based_mastery_estimator.estimate = MagicMock(
            return_value=MasteryResult(mastery_score=0.5)
        )
        engine.ml_mastery_estimator.estimate = MagicMock()
        engine.strategy_selector.model_path = Path("missing-model.pkl")

        result = engine.recommend(1, 2, 1102)

        self.assertIsNotNone(result)
        engine.rule_based_mastery_estimator.estimate.assert_called_once()
        engine.ml_mastery_estimator.estimate.assert_not_called()

    def test_ml_used_for_high_interactions_when_strategy_selects_ml(self):
        engine = self._build_engine(
            [self._interaction(score=1.0, difficulty=0.7) for _ in range(12)]
        )
        engine.strategy_selector.select = MagicMock(return_value="ml")
        engine.ml_mastery_estimator.estimate = MagicMock(
            return_value=MasteryResult(mastery_score=0.8)
        )
        engine.rule_based_mastery_estimator.estimate = MagicMock(
            return_value=MasteryResult(mastery_score=0.4)
        )

        result = engine.recommend(1, 2, 1102)

        self.assertIsNotNone(result)
        engine.ml_mastery_estimator.estimate.assert_called_once()
        engine.rule_based_mastery_estimator.estimate.assert_not_called()

        ml_features = engine.ml_mastery_estimator.estimate.call_args.args[0]
        self.assertEqual(ml_features["attempt_count_on_topic"], 12)
        self.assertEqual(ml_features["subject_id"], 2)
        self.assertEqual(ml_features["topic_id"], 1102)
        self.assertEqual(ml_features["question_difficulty"], 0.7)

    def test_fallback_to_rule_based_if_ml_fails(self):
        engine = self._build_engine(
            [self._interaction() for _ in range(12)]
        )
        engine.strategy_selector.select = MagicMock(return_value="ml")
        engine.ml_mastery_estimator.estimate = MagicMock(
            side_effect=Exception("ML crash")
        )
        engine.rule_based_mastery_estimator.estimate = MagicMock(
            return_value=MasteryResult(mastery_score=0.4)
        )

        result = engine.recommend(1, 2, 1102)

        self.assertIsNotNone(result)
        engine.ml_mastery_estimator.estimate.assert_called_once()
        engine.rule_based_mastery_estimator.estimate.assert_called_once()
