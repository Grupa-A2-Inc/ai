import csv
from pathlib import Path
import tempfile

from django.test import TestCase

from tutoring.ml.dataset_builder import StudentMasteryDatasetBuilder
from tutoring.models import (
    Question,
    QuestionType,
    StudentInteraction,
    StudentProfile,
    StudentTopicLevel,
)


class StudentMasteryDatasetBuilderTests(TestCase):
    def test_build_dataset_writes_rows_with_history_and_mastery_defaults(self):
        question = Question.objects.create(
            subject_id=2,
            topic_id=1102,
            question_type=QuestionType.SINGLE_CHOICE,
            content="What is 2 + 2?",
            difficulty=0.7,
        )
        student = StudentProfile.objects.create(student_id="student-1")
        StudentTopicLevel.objects.create(
            student=student,
            subject_id=2,
            topic_id=1102,
            mastery_score=0.8,
        )
        StudentInteraction.objects.create(
            user_id="student-1",
            question=question,
            is_correct=True,
            score=1.0,
            time_spent=30.0,
        )
        StudentInteraction.objects.create(
            user_id="student-1",
            question=question,
            is_correct=False,
            score=0.0,
            time_spent=150.0,
        )
        StudentInteraction.objects.create(
            user_id="student-2",
            question=question,
            is_correct=True,
            score=0.5,
            time_spent=60.0,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "dataset.csv"

            StudentMasteryDatasetBuilder().build_dataset(str(output_path))

            with output_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["student_id"], "student-1")
        self.assertEqual(rows[0]["attempt_count_on_topic"], "0")
        self.assertEqual(rows[0]["average_score_on_topic"], "0.5")
        self.assertEqual(rows[0]["current_mastery"], "0.8")
        self.assertEqual(rows[1]["attempt_count_on_topic"], "1")
        self.assertEqual(rows[1]["average_score_on_topic"], "1.0")
        self.assertEqual(rows[1]["normalized_time"], "1.0")
        self.assertEqual(rows[2]["student_id"], "student-2")
        self.assertEqual(rows[2]["current_mastery"], "0.5")

    def test_calculate_target_mastery_is_clamped(self):
        builder = StudentMasteryDatasetBuilder()

        self.assertEqual(
            builder._calculate_target_mastery(
                current_mastery=2.0,
                average_score=1.0,
                normalized_average_time=0.0,
            ),
            1.0,
        )
        self.assertEqual(
            builder._calculate_target_mastery(
                current_mastery=-1.0,
                average_score=0.0,
                normalized_average_time=1.0,
            ),
            0.0,
        )
