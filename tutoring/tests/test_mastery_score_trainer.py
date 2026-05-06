from pathlib import Path
import tempfile

import pandas as pd
from django.test import TestCase

from tutoring.ml.train_mastery_model import MasteryModelTrainer


class MasteryModelTrainerTests(TestCase):
    def test_train_saves_model_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            dataset_path = Path(temporary_directory) / "dataset.csv"
            model_path = Path(temporary_directory) / "mastery_model.pkl"

            dataset = pd.DataFrame(
                [
                    {
                        "subject_id": 2,
                        "topic_id": 1102,
                        "question_difficulty": 0.5,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 40.0,
                        "normalized_time": 0.33,
                        "attempt_count_on_topic": 1,
                        "average_score_on_topic": 0.8,
                        "average_time_on_topic": 45.0,
                        "normalized_average_time": 0.37,
                        "recent_average_score": 0.8,
                        "recent_average_time": 45.0,
                        "normalized_recent_time": 0.37,
                        "current_mastery": 0.5,
                        "target_mastery": 0.6,
                    },
                    {
                        "subject_id": 2,
                        "topic_id": 1102,
                        "question_difficulty": 0.7,
                        "score": 0.0,
                        "is_correct": 0,
                        "time_spent": 90.0,
                        "normalized_time": 0.75,
                        "attempt_count_on_topic": 2,
                        "average_score_on_topic": 0.5,
                        "average_time_on_topic": 65.0,
                        "normalized_average_time": 0.54,
                        "recent_average_score": 0.5,
                        "recent_average_time": 65.0,
                        "normalized_recent_time": 0.54,
                        "current_mastery": 0.6,
                        "target_mastery": 0.52,
                    },
                    {
                        "subject_id": 3,
                        "topic_id": 1201,
                        "question_difficulty": 0.3,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 30.0,
                        "normalized_time": 0.25,
                        "attempt_count_on_topic": 3,
                        "average_score_on_topic": 0.9,
                        "average_time_on_topic": 35.0,
                        "normalized_average_time": 0.29,
                        "recent_average_score": 0.9,
                        "recent_average_time": 35.0,
                        "normalized_recent_time": 0.29,
                        "current_mastery": 0.7,
                        "target_mastery": 0.75,
                    },
                    {
                        "subject_id": 3,
                        "topic_id": 1201,
                        "question_difficulty": 0.8,
                        "score": 0.5,
                        "is_correct": 0,
                        "time_spent": 100.0,
                        "normalized_time": 0.83,
                        "attempt_count_on_topic": 4,
                        "average_score_on_topic": 0.6,
                        "average_time_on_topic": 70.0,
                        "normalized_average_time": 0.58,
                        "recent_average_score": 0.6,
                        "recent_average_time": 70.0,
                        "normalized_recent_time": 0.58,
                        "current_mastery": 0.55,
                        "target_mastery": 0.53,
                    },
                    {
                        "subject_id": 4,
                        "topic_id": 1301,
                        "question_difficulty": 0.4,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 25.0,
                        "normalized_time": 0.2,
                        "attempt_count_on_topic": 5,
                        "average_score_on_topic": 0.85,
                        "average_time_on_topic": 32.0,
                        "normalized_average_time": 0.26,
                        "recent_average_score": 0.85,
                        "recent_average_time": 32.0,
                        "normalized_recent_time": 0.26,
                        "current_mastery": 0.65,
                        "target_mastery": 0.72,
                    },
                ]
            )

            dataset.to_csv(dataset_path, index=False)

            trainer = MasteryModelTrainer()

            result = trainer.train(
                dataset_path=str(dataset_path),
                model_output_path=str(model_path),
            )

            self.assertTrue(model_path.exists())
            self.assertIn("best_model", result)
            self.assertIn("metrics", result)
            self.assertIn("all_results", result)