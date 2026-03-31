from dataclasses import dataclass
from typing import List

from tutoring.dto.topic_features import TopicFeatures
from tutoring.services.feature_engineering_service import FeatureEngineeringService


@dataclass
class DummyInteraction:
    is_correct: bool
    time_spent: float


@dataclass
class DummyStudentContext:
    history: List[DummyInteraction]


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