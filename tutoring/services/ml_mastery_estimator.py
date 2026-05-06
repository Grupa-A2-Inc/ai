from tutoring.ml.mastery_model_loader import MasteryModelLoader


class ModelNotAvailableError(Exception):
    pass


class MLMasteryEstimator:
    def __init__(self):
        self.model_loader = MasteryModelLoader()

    def estimate(self, features):
        model = self.model_loader.load()

        if model is None:
            raise ModelNotAvailableError("ML model not found")

        input_row = self._build_model_input(features)

        prediction = model.predict([input_row])[0]
        prediction = max(0.0, min(float(prediction), 1.0))

        return {
            "mastery_score": prediction
        }

    def _build_model_input(self, features):
        return [
            features["subject_id"],
            features["topic_id"],
            features["question_difficulty"],
            features["score"],
            features["is_correct"],
            features["time_spent"],
            features["normalized_time"],
            features["attempt_count_on_topic"],
            features["average_score_on_topic"],
            features["average_time_on_topic"],
            features["normalized_average_time"],
            features["recent_average_score"],
            features["recent_average_time"],
            features["normalized_recent_time"],
            features["current_mastery"],
        ]