from dataclasses import dataclass
from types import SimpleNamespace
from typing import List

from tutoring.dto.topic_features import TopicFeatures
from tutoring.services.feature_engineering_service import FeatureEngineeringService


@dataclass
class DummyInteraction:
    is_correct: bool
    time_spent: float
    score: float = 0.0
    question: object = None


@dataclass
class DummyStudentContext:
    history: List[DummyInteraction]
    topic_mastery_score: float = 0.5
    recent_history: List[DummyInteraction] = None


class TestFeatureEngineeringService:
    def setup_method(self):
        self.service = FeatureEngineeringService()

    def test_returns_correct_features_for_good_student(self):
        history = [
            DummyInteraction(is_correct=True, time_spent=20.0),
            DummyInteraction(is_correct=True, time_spent=25.0),
            DummyInteraction(is_correct=True, time_spent=30.0),
        ]
        student_context = DummyStudentContext(history=history)

        features = self.service.build_features(student_context)

        assert features.accuracy == 1.0
        assert features.avg_time == 25.0
        assert features.attempt_count == 3

    def test_returns_correct_features_for_average_student(self):
        history = [
            DummyInteraction(is_correct=True, time_spent=20.0),
            DummyInteraction(is_correct=False, time_spent=40.0),
        ]
        student_context = DummyStudentContext(history=history)

        features = self.service.build_features(student_context)

        assert features.accuracy == 0.5
        assert features.avg_time == 30.0
        assert features.attempt_count == 2

    def test_returns_default_features_for_new_student_without_history(self):
        student_context = DummyStudentContext(history=[])

        features = self.service.build_features(student_context)

        assert features.accuracy == 0.5
        assert features.avg_time == 30.0
        assert features.attempt_count == 0

    def test_uses_topic_mastery_for_student_without_history(self):
        student_context = DummyStudentContext(
            history=[],
            topic_mastery_score=0.8,
        )

        features = self.service.build_features(student_context)

        assert features.accuracy == 0.8
        assert features.avg_time == 30.0
        assert features.attempt_count == 0

    def test_returns_zero_accuracy_for_student_with_all_wrong_answers(self):
        history = [
            DummyInteraction(is_correct=False, time_spent=15.0),
            DummyInteraction(is_correct=False, time_spent=25.0),
        ]
        student_context = DummyStudentContext(history=history)

        features = self.service.build_features(student_context)

        assert features.accuracy == 0.0
        assert features.avg_time == 20.0
        assert features.attempt_count == 2

    def test_build_ml_features_matches_training_columns(self):
        question = type("Question", (), {"difficulty": 0.7})()
        history = [
            DummyInteraction(
                is_correct=True,
                score=1.0,
                time_spent=30.0,
                question=question,
            ),
            DummyInteraction(
                is_correct=False,
                score=0.0,
                time_spent=90.0,
                question=question,
            ),
        ]
        student_context = DummyStudentContext(
            history=history,
            recent_history=history,
            topic_mastery_score=0.65,
        )

        features = self.service.build_ml_features(
            student_context=student_context,
            subject_id=2,
            topic_id=1102,
        )

        assert features == {
            "subject_id": 2,
            "topic_id": 1102,
            "question_difficulty": 0.7,
            "score": 0.0,
            "is_correct": 0,
            "time_spent": 90.0,
            "normalized_time": 0.75,
            "attempt_count_on_topic": 2,
            "average_score_on_topic": 0.5,
            "average_time_on_topic": 60.0,
            "normalized_average_time": 0.5,
            "recent_average_score": 0.5,
            "recent_average_time": 60.0,
            "normalized_recent_time": 0.5,
            "current_mastery": 0.65,
        }

    def test_build_ml_features_uses_defaults_for_empty_history(self):
        student_context = DummyStudentContext(
            history=[],
            recent_history=[],
            topic_mastery_score=0.7,
        )

        features = self.service.build_ml_features(
            student_context=student_context,
            subject_id=2,
            topic_id=1102,
        )

        assert features["question_difficulty"] == 0.5
        assert features["score"] == 0.7
        assert features["is_correct"] == 0
        assert features["time_spent"] == 60.0
        assert features["current_mastery"] == 0.7

    def test_build_ml_features_falls_back_to_correctness_when_score_missing(self):
        interaction = SimpleNamespace(
            is_correct=True,
            time_spent=240.0,
            question=SimpleNamespace(),
        )
        student_context = DummyStudentContext(
            history=[interaction],
            recent_history=None,
        )

        features = self.service.build_ml_features(
            student_context=student_context,
            subject_id=2,
            topic_id=1102,
        )

        assert features["score"] == 1.0
        assert features["normalized_time"] == 1.0
        assert features["question_difficulty"] == 0.5

    def test_interaction_helpers_return_defaults_for_none(self):
        assert self.service._score_for_interaction(None) == 0.5
        assert self.service._time_for_interaction(None) == 60.0
