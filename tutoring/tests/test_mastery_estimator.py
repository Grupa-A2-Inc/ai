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