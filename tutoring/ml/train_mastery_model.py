from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


class MasteryModelTrainer:
    TARGET_COLUMN = "target_mastery"

    FEATURE_COLUMNS = [
        "subject_id",
        "topic_id",
        "question_difficulty",
        "score",
        "is_correct",
        "time_spent",
        "normalized_time",
        "attempt_count_on_topic",
        "average_score_on_topic",
        "average_time_on_topic",
        "normalized_average_time",
        "recent_average_score",
        "recent_average_time",
        "normalized_recent_time",
        "current_mastery",
    ]

    def train(
        self,
        dataset_path: str,
        model_output_path: str,
    ) -> dict:
        dataset = self._load_dataset(dataset_path)

        self._validate_dataset(dataset)

        features = dataset[self.FEATURE_COLUMNS]
        target = dataset[self.TARGET_COLUMN]

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=42,
        )

        candidate_models = self._build_candidate_models()

        results = []

        for model_name, model in candidate_models.items():
            model.fit(x_train, y_train)

            predictions = model.predict(x_test)
            predictions = self._clamp_predictions(predictions)

            metrics = self._calculate_metrics(
                y_true=y_test,
                y_pred=predictions,
            )

            results.append(
                {
                    "name": model_name,
                    "model": model,
                    "metrics": metrics,
                }
            )

        best_result = self._select_best_model(results)

        self._save_model(
            model=best_result["model"],
            output_path=model_output_path,
        )

        return {
            "best_model": best_result["name"],
            "metrics": best_result["metrics"],
            "all_results": [
                {
                    "name": result["name"],
                    "metrics": result["metrics"],
                }
                for result in results
            ],
        }

    def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        return pd.read_csv(dataset_path)

    def _validate_dataset(self, dataset: pd.DataFrame) -> None:
        missing_columns = []

        for column in self.FEATURE_COLUMNS + [self.TARGET_COLUMN]:
            if column not in dataset.columns:
                missing_columns.append(column)

        if missing_columns:
            raise ValueError(
                f"Dataset is missing required columns: {missing_columns}"
            )

        if dataset.empty:
            raise ValueError("Dataset is empty. Cannot train ML model.")

    def _build_candidate_models(self) -> dict:
        return {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                random_state=42,
            ),
        }

    def _calculate_metrics(self, y_true, y_pred) -> dict:
        return {
            "mae": mean_absolute_error(y_true, y_pred),
            "mse": mean_squared_error(y_true, y_pred),
            "r2": r2_score(y_true, y_pred),
        }

    def _select_best_model(self, results: list[dict]) -> dict:
        return min(
            results,
            key=lambda result: result["metrics"]["mae"],
        )

    def _save_model(self, model, output_path: str) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, output_file)

    def _clamp_predictions(self, predictions):
        return [
            max(0.0, min(float(prediction), 1.0))
            for prediction in predictions
        ]