import os

from django.core.management.base import BaseCommand

from tutoring.ml.train_mastery_model import MasteryModelTrainer


class Command(BaseCommand):
    help = "Train ML mastery model from exported dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            default="data/training/student_mastery_dataset.csv",
        )

        parser.add_argument(
            "--output",
            type=str,
            default=(
                os.getenv("MASTERY_MODEL_PATH")
                or "tutoring/models_store/mastery_model.pkl"
            ),
        )

    def handle(self, *args, **options):
        dataset_path = options["dataset"]
        output_path = options["output"]

        trainer = MasteryModelTrainer()

        result = trainer.train(
            dataset_path=dataset_path,
            model_output_path=output_path,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Best model: {result['best_model']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Metrics: {result['metrics']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Model saved to {output_path}"
            )
        )

        self.stdout.write("All model results:")

        for model_result in result["all_results"]:
            self.stdout.write(
                f"{model_result['name']}: {model_result['metrics']}"
            )
