from tutoring.services.mastery_estimator import MasteryEstimator


class DummyNormalizedFeatures:
    def __init__(self, accuracy, avg_time):
        self.accuracy = accuracy
        self.avg_time = avg_time


def test_mastery_high_for_good_student():
    features = DummyNormalizedFeatures(
        accuracy=0.9,
        avg_time=0.2,  # low time → good
    )

    estimator = MasteryEstimator()
    result = estimator.estimate(features)

    assert 0.8 <= result.mastery_score <= 1.0


def test_mastery_medium_for_average_student():
    features = DummyNormalizedFeatures(
        accuracy=0.6,
        avg_time=0.5,
    )

    estimator = MasteryEstimator()
    result = estimator.estimate(features)

    assert 0.4 <= result.mastery_score <= 0.7


def test_mastery_low_for_weak_student():
    features = DummyNormalizedFeatures(
        accuracy=0.3,
        avg_time=0.9,  # slow → bad
    )

    estimator = MasteryEstimator()
    result = estimator.estimate(features)

    assert 0.0 <= result.mastery_score <= 0.4


def test_mastery_clamped_between_0_and_1():
    features = DummyNormalizedFeatures(
        accuracy=2.0,   # unrealistic
        avg_time=-1.0,  # unrealistic
    )

    estimator = MasteryEstimator()
    result = estimator.estimate(features)

    assert 0.0 <= result.mastery_score <= 1.0

@dataclass
class NormalizedFeatures:
    accuracy: float
    avg_time: float
    attempt_count: int = 0


class TestMasteryEstimator:
    def setup_method(self):
        self.estimator = MasteryEstimator()

    def test_returns_expected_score_for_typical_case(self):
        features = NormalizedFeatures(
            accuracy=0.8,
            avg_time=0.4,
            attempt_count=10,
        )

        result = self.estimator.estimate(features)

        expected = 0.7 * 0.8 + 0.3 * (1 - 0.4)
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)

    def test_returns_high_score_for_good_accuracy_and_fast_time(self):
        features = NormalizedFeatures(
            accuracy=0.9,
            avg_time=0.1,
            attempt_count=12,
        )

        result = self.estimator.estimate(features)

        expected = 0.7 * 0.9 + 0.3 * (1 - 0.1)
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)
        assert result.mastery_score > 0.8

    def test_returns_low_score_for_bad_accuracy_and_slow_time(self):
        features = NormalizedFeatures(
            accuracy=0.2,
            avg_time=0.9,
            attempt_count=8,
        )

        result = self.estimator.estimate(features)

        expected = 0.7 * 0.2 + 0.3 * (1 - 0.9)
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)
        assert result.mastery_score < 0.2

    def test_returns_neutral_score_for_new_student_like_case(self):
        features = NormalizedFeatures(
            accuracy=0.5,
            avg_time=0.5,
            attempt_count=0,
        )

        result = self.estimator.estimate(features)

        expected = 0.7 * 0.5 + 0.3 * (1 - 0.5)
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)
        assert math.isclose(result.mastery_score, 0.5, rel_tol=1e-9)

    def test_returns_one_when_accuracy_is_one_and_time_is_best(self):
        features = NormalizedFeatures(
            accuracy=1.0,
            avg_time=0.0,
            attempt_count=15,
        )

        result = self.estimator.estimate(features)

        expected = 1.0
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)

    def test_returns_zero_when_accuracy_is_zero_and_time_is_worst(self):
        features = NormalizedFeatures(
            accuracy=0.0,
            avg_time=1.0,
            attempt_count=15,
        )

        result = self.estimator.estimate(features)

        expected = 0.0
        assert math.isclose(result.mastery_score, expected, rel_tol=1e-9)

    def test_fast_time_should_increase_mastery_when_accuracy_is_same(self):
        fast_features = NormalizedFeatures(
            accuracy=0.7,
            avg_time=0.2,
            attempt_count=10,
        )
        slow_features = NormalizedFeatures(
            accuracy=0.7,
            avg_time=0.8,
            attempt_count=10,
        )

        fast_result = self.estimator.estimate(fast_features)
        slow_result = self.estimator.estimate(slow_features)

        assert fast_result.mastery_score > slow_result.mastery_score

    def test_better_accuracy_should_outweigh_same_time(self):
        weak_features = NormalizedFeatures(
            accuracy=0.4,
            avg_time=0.3,
            attempt_count=10,
        )
        strong_features = NormalizedFeatures(
            accuracy=0.8,
            avg_time=0.3,
            attempt_count=10,
        )

        weak_result = self.estimator.estimate(weak_features)
        strong_result = self.estimator.estimate(strong_features)

        assert strong_result.mastery_score > weak_result.mastery_score

    def test_result_is_clamped_when_values_are_out_of_range_high(self):
        features = NormalizedFeatures(
            accuracy=1.5,
            avg_time=-0.2,
            attempt_count=5,
        )

        result = self.estimator.estimate(features)

        assert 0.0 <= result.mastery_score <= 1.0
        assert math.isclose(result.mastery_score, 1.0, rel_tol=1e-9)

    def test_result_is_clamped_when_values_are_out_of_range_low(self):
        features = NormalizedFeatures(
            accuracy=-0.5,
            avg_time=1.5,
            attempt_count=5,
        )

        result = self.estimator.estimate(features)

        assert 0.0 <= result.mastery_score <= 1.0
        assert math.isclose(result.mastery_score, 0.0, rel_tol=1e-9)