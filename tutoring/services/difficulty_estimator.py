class BaseDifficultyEstimator:
    def estimate(self, features, mastery):
        raise NotImplementedError


class RuleBasedDifficultyEstimator(BaseDifficultyEstimator):
    def estimate(self, features, mastery):
        pass