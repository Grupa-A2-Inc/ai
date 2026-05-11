import os
from pathlib import Path

import joblib


class MasteryModelLoader:
    DEFAULT_MODEL_PATH = "tutoring/models_store/mastery_model.pkl"

    def __init__(
        self,
        model_path: str | None = None,
    ):
        self.model_path = Path(
            model_path
            or os.getenv("MASTERY_MODEL_PATH")
            or self.DEFAULT_MODEL_PATH
        )
        self._model = None

    def load(self):
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            return None

        self._model = joblib.load(self.model_path)

        return self._model
