import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tutoring.models import (
    Question,
    QuestionOption,
    QuestionCorrectOption,
    QuestionType,
)


class Command(BaseCommand):
    help = "Import questions from all JSON files in a folder into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "folder_path",
            type=str,
            help="Path to the folder containing JSON files with questions."
        )

    def handle(self, *args, **options):
        folder_path = Path(options["folder_path"])

        if not folder_path.exists():
            raise CommandError(f"Folder does not exist: {folder_path}")

        if not folder_path.is_dir():
            raise CommandError(f"Provided path is not a folder: {folder_path}")

        json_files = sorted(folder_path.rglob("*.json"))

        if not json_files:
            raise CommandError(f"No JSON files found in folder: {folder_path}")

        total_created = 0
        total_updated = 0
        successful_files = []
        failed_files = []

        for json_file in json_files:
            self.stdout.write(f"Processing file: {json_file}")

            try:
                file_created, file_updated = self._process_file(json_file)
                total_created += file_created
                total_updated += file_updated

                successful_files.append(
                    {
                        "file": str(json_file),
                        "created": file_created,
                        "updated": file_updated,
                    }
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Finished {json_file.name} -> Created: {file_created}, Updated: {file_updated}"
                    )
                )

            except Exception as exc:
                failed_files.append(
                    {
                        "file": str(json_file),
                        "error": str(exc),
                    }
                )

                self.stdout.write(
                    self.style.ERROR(
                        f"Failed {json_file.name} -> {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))
        self.stdout.write(f"Successful files: {len(successful_files)}")
        self.stdout.write(f"Failed files: {len(failed_files)}")
        self.stdout.write(f"Total created: {total_created}")
        self.stdout.write(f"Total updated: {total_updated}")

        if successful_files:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Successful files details:"))
            for file_info in successful_files:
                self.stdout.write(
                    f"- {file_info['file']} -> Created: {file_info['created']}, Updated: {file_info['updated']}"
                )

        if failed_files:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Failed files details:"))
            for file_info in failed_files:
                self.stdout.write(
                    f"- {file_info['file']} -> Error: {file_info['error']}"
                )

    def _process_file(self, json_file: Path) -> tuple[int, int]:
        try:
            with json_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in file {json_file.name}: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError(
                f"JSON root must be a list of question objects in file {json_file.name}."
            )

        file_created = 0
        file_updated = 0

        for question_data in payload:
            with transaction.atomic():
                was_created = self._import_question(question_data)
                if was_created:
                    file_created += 1
                else:
                    file_updated += 1

        return file_created, file_updated

    def _import_question(self, question_data: dict) -> bool:
        self._validate_question_payload(question_data)

        question_id = question_data["question_id"]
        subject_id = question_data["subject_id"]
        topic_id = question_data["topic_id"]
        question_type = question_data["question_type"]
        content = question_data["content"]
        difficulty = question_data["difficulty"]
        is_active = question_data["is_active"]

        question, created = Question.objects.update_or_create(
            id=question_id,
            defaults={
                "subject_id": subject_id,
                "topic_id": topic_id,
                "question_type": question_type,
                "content": content,
                "difficulty": difficulty,
                "is_active": is_active,
            },
        )

        self._replace_options_and_correct_answers(question, question_data)

        return created

    def _replace_options_and_correct_answers(self, question: Question, question_data: dict) -> None:
        options_data = question_data["options"]
        correct_option_ids = set(question_data["correct_option_ids"])

        QuestionCorrectOption.objects.filter(question=question).delete()
        QuestionOption.objects.filter(question=question).delete()

        created_options_by_id = {}

        for option_data in options_data:
            option = QuestionOption.objects.create(
                id=option_data["option_id"],
                question=question,
                text=option_data["text"],
                display_order=option_data["display_order"],
            )
            created_options_by_id[option.id] = option

        for option_id in correct_option_ids:
            if option_id not in created_options_by_id:
                raise CommandError(
                    f"Question {question.id}: correct option id {option_id} does not exist in options."
                )

            QuestionCorrectOption.objects.create(
                question=question,
                option=created_options_by_id[option_id],
            )

    def _validate_question_payload(self, question_data: dict) -> None:
        required_fields = [
            "question_id",
            "subject_id",
            "topic_id",
            "question_type",
            "content",
            "difficulty",
            "is_active",
            "options",
            "correct_option_ids",
        ]

        for field_name in required_fields:
            if field_name not in question_data:
                raise CommandError(f"Missing required field: {field_name}")

        if question_data["question_type"] not in {
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
        }:
            raise CommandError(
                f"Invalid question_type: {question_data['question_type']}"
            )

        difficulty = question_data["difficulty"]
        if not isinstance(difficulty, (int, float)):
            raise CommandError("Field 'difficulty' must be numeric.")

        if not 0.0 <= float(difficulty) <= 1.0:
            raise CommandError("Field 'difficulty' must be between 0.0 and 1.0.")

        options = question_data["options"]
        correct_option_ids = question_data["correct_option_ids"]

        if not isinstance(options, list) or len(options) < 2:
            raise CommandError("Field 'options' must be a list with at least 2 items.")

        if not isinstance(correct_option_ids, list) or len(correct_option_ids) < 1:
            raise CommandError(
                "Field 'correct_option_ids' must be a list with at least 1 item."
            )

        option_ids = set()

        for option in options:
            for option_field in ["option_id", "text", "display_order"]:
                if option_field not in option:
                    raise CommandError(
                        f"Option is missing required field: {option_field}"
                    )

            option_id = option["option_id"]

            if option_id in option_ids:
                raise CommandError(
                    f"Duplicate option_id {option_id} in question {question_data['question_id']}."
                )

            option_ids.add(option_id)

        for correct_option_id in correct_option_ids:
            if correct_option_id not in option_ids:
                raise CommandError(
                    f"correct_option_id {correct_option_id} not found in options "
                    f"for question {question_data['question_id']}."
                )

        if question_data["question_type"] == QuestionType.SINGLE_CHOICE:
            if len(correct_option_ids) != 1:
                raise CommandError(
                    f"Question {question_data['question_id']} is single_choice "
                    f"but has {len(correct_option_ids)} correct options."
                )