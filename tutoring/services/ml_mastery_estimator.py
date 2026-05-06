import pandas as pd

from tutoring.dto.mastery_result import MasteryResult
from tutoring.ml.mastery_model_loader import MasteryModelLoader
from tutoring.ml.train_mastery_model import MasteryModelTrainer


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

        prediction = model.predict(input_row)[0]
        prediction = max(0.0, min(float(prediction), 1.0))

        return MasteryResult(mastery_score=prediction)

    def _build_model_input(self, features):
        return pd.DataFrame(
            [
                {
                    column: features[column]
                    for column in MasteryModelTrainer.FEATURE_COLUMNS
                }
            ],
            columns=MasteryModelTrainer.FEATURE_COLUMNS,
        )
