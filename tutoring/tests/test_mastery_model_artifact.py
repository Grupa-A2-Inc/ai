from pathlib import Path

from django.test import SimpleTestCase

from tutoring.dto.mastery_result import MasteryResult
from tutoring.ml.mastery_model_loader import MasteryModelLoader
from tutoring.services.ml_mastery_estimator import (
    MLMasteryEstimator,
    ModelNotAvailableError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "tutoring" / "models_store" / "mastery_model.pkl"


def base_features() -> dict:
    return {
        "subject_id": 2,
        "topic_id": 1102,
        "question_difficulty": 0.5,
        "score": 0.5,
        "is_correct": 0,
        "time_spent": 60.0,
        "normalized_time": 0.5,
        "attempt_count_on_topic": 12,
        "average_score_on_topic": 0.5,
        "average_time_on_topic": 60.0,
        "normalized_average_time": 0.5,
        "recent_average_score": 0.5,
        "recent_average_time": 60.0,
        "normalized_recent_time": 0.5,
        "current_mastery": 0.5,
    }


class MasteryModelArtifactTests(SimpleTestCase):
    def test_mastery_model_file_exists(self):
        self.assertTrue(
            MODEL_PATH.exists(),
            "Expected trained model at tutoring/models_store/mastery_model.pkl",
        )

    def test_loader_loads_and_caches_model(self):
        loader = MasteryModelLoader(model_path=str(MODEL_PATH))

        first_model = loader.load()
        second_model = loader.load()

        self.assertIsNotNone(first_model)
        self.assertIs(first_model, second_model)
        self.assertTrue(hasattr(first_model, "predict"))

    def test_loader_returns_none_when_model_file_is_missing(self):
        loader = MasteryModelLoader(model_path="missing-model.pkl")

        self.assertIsNone(loader.load())

    def test_estimator_raises_when_model_file_is_missing(self):
        estimator = MLMasteryEstimator()
        estimator.model_loader = MasteryModelLoader(model_path="missing-model.pkl")

        with self.assertRaises(ModelNotAvailableError):
            estimator.estimate(base_features())

    def test_estimator_returns_clamped_mastery_result(self):
        estimator = MLMasteryEstimator()
        estimator.model_loader = MasteryModelLoader(model_path=str(MODEL_PATH))

        result = estimator.estimate(base_features())

        self.assertIsInstance(result, MasteryResult)
        self.assertGreaterEqual(result.mastery_score, 0.0)
        self.assertLessEqual(result.mastery_score, 1.0)

    def test_model_predicts_higher_mastery_for_stronger_profile(self):
        estimator = MLMasteryEstimator()
        estimator.model_loader = MasteryModelLoader(model_path=str(MODEL_PATH))

        low_profile = base_features() | {
            "score": 0.0,
            "is_correct": 0,
            "time_spent": 105.0,
            "normalized_time": 0.875,
            "average_score_on_topic": 0.2,
            "average_time_on_topic": 100.0,
            "normalized_average_time": 0.8333,
            "recent_average_score": 0.1,
            "recent_average_time": 105.0,
            "normalized_recent_time": 0.875,
            "current_mastery": 0.25,
        }
        high_profile = base_features() | {
            "score": 1.0,
            "is_correct": 1,
            "time_spent": 25.0,
            "normalized_time": 0.2083,
            "average_score_on_topic": 0.9,
            "average_time_on_topic": 35.0,
            "normalized_average_time": 0.2917,
            "recent_average_score": 0.95,
            "recent_average_time": 30.0,
            "normalized_recent_time": 0.25,
            "current_mastery": 0.82,
        }

        low_result = estimator.estimate(low_profile)
        high_result = estimator.estimate(high_profile)

        self.assertLess(low_result.mastery_score, 0.4)
        self.assertGreater(high_result.mastery_score, 0.7)
        self.assertGreater(
            high_result.mastery_score,
            low_result.mastery_score,
        )
