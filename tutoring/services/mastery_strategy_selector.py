from pathlib import Path


class MasteryStrategySelector:
    MIN_INTERACTIONS = 10

    def __init__(self):
        self.model_path = Path("tutoring/models_store/mastery_model.pkl")

    def select(self, features):
        attempt_count = features["attempt_count_on_topic"]

        if attempt_count < self.MIN_INTERACTIONS:
            return "rule_based"

        if not self.model_path.exists():
            return "rule_based"

        return "ml"