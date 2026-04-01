import unittest

from tutoring.services.difficulty_estimator import DifficultyEstimator


class TestDifficultyEstimator(unittest.TestCase):

    def setUp(self):
        self.estimator = DifficultyEstimator()

    def test_mastery_0_3(self):
        mastery = 0.3
        result = self.estimator.estimate(mastery)

        self.assertAlmostEqual(result.target_difficulty, 0.4)

    def test_mastery_0_8(self):
        mastery = 0.8
        result = self.estimator.estimate(mastery)

        self.assertAlmostEqual(result.target_difficulty, 0.9)

    def test_mastery_0_95(self):
        mastery = 0.95
        result = self.estimator.estimate(mastery)

        self.assertAlmostEqual(result.target_difficulty, 1.0)


if __name__ == "__main__":
    unittest.main()