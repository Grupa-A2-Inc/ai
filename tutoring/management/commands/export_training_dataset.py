from django.core.management.base import BaseCommand

from tutoring.ml.dataset_builder import StudentMasteryDatasetBuilder


class Command(BaseCommand):
    help = "Export ML training dataset from StudentInteraction."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="data/training/student_mastery_dataset.csv",
        )

    def handle(self, *args, **options):
        output_path = options["output"]

        builder = StudentMasteryDatasetBuilder()
        builder.build_dataset(output_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"Training dataset exported successfully to {output_path}"
            )
        )