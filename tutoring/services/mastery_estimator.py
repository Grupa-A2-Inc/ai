class BaseMasteryEstimator:
    def estimate(self, user_id, subject_id, topic_id, features):
        raise NotImplementedError


class RuleBasedMasteryEstimator(BaseMasteryEstimator):
    def estimate(self, user_id, subject_id, topic_id, features):
        pass