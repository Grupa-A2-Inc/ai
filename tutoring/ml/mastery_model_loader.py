from pathlib import Path

import joblib


class MasteryModelLoader:
    def __init__(
        self,
        model_path: str = "tutoring/models_store/mastery_model.pkl",
    ):
        self.model_path = Path(model_path)
        self._model = None

    def load(self):
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            return None

        self._model = joblib.load(self.model_path)

        return self._model