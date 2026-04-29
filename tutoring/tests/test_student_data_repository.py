from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from tutoring.models import Question, QuestionType, StudentInteraction
from tutoring.repositories.student_data_repository import StudentDataRepository


class StudentDataRepositoryTests(TestCase):
    def setUp(self):
        self.repository = StudentDataRepository()

        self.question_easy = Question.objects.create(
            subject_id=3,
            topic_id=8,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Q1",
            difficulty=0.2,
            is_active=True,
        )

        self.question_medium = Question.objects.create(
            subject_id=3,
            topic_id=8,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Q2",
            difficulty=0.5,
            is_active=True,
        )

        self.question_hard = Question.objects.create(
            subject_id=3,
            topic_id=8,
            question_type=QuestionType.MULTIPLE_CHOICE,
            content="Q3",
            difficulty=0.8,
            is_active=True,
        )

        self.inactive_question = Question.objects.create(
            subject_id=3,
            topic_id=8,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Q4",
            difficulty=0.6,
            is_active=False,
        )

        # User 12 answered question_easy twice and question_medium once
        now = timezone.now()

        self.first_interaction = StudentInteraction.objects.create(
            user_id=12,
            question=self.question_easy,
            is_correct=True,
            score=1.0,
            time_spent=30.0,
        )

        self.second_interaction = StudentInteraction.objects.create(
            user_id=12,
            question=self.question_easy,
            is_correct=False,
            score=0.0,
            time_spent=45.0,
        )

        self.third_interaction = StudentInteraction.objects.create(
            user_id=12,
            question=self.question_medium,
            is_correct=True,
            score=1.0,
            time_spent=20.0,
        )

        StudentInteraction.objects.filter(id=self.first_interaction.id).update(
            created_at=now - timedelta(minutes=3)
        )
        StudentInteraction.objects.filter(id=self.second_interaction.id).update(
            created_at=now - timedelta(minutes=2)
        )
        StudentInteraction.objects.filter(id=self.third_interaction.id).update(
            created_at=now - timedelta(minutes=1)
        )

        self.first_interaction.refresh_from_db()
        self.second_interaction.refresh_from_db()
        self.third_interaction.refresh_from_db()

    def test_get_student_history_returns_correct_interactions(self):
        student_history = self.repository.get_student_history(
            user_id=12,
            subject_id=3,
            topic_id=8,
        )

        self.assertEqual(student_history.count(), 3)

    def test_get_seen_question_ids_returns_unique_ids(self):
        seen_question_ids = self.repository.get_seen_question_ids(
            user_id=12,
            subject_id=3,
            topic_id=8,
        )

        self.assertEqual(len(seen_question_ids), len(set(seen_question_ids)))
        self.assertIn(self.question_easy.id, seen_question_ids)
        self.assertIn(self.question_medium.id, seen_question_ids)
        self.assertNotIn(self.question_hard.id, seen_question_ids)

    def test_get_recent_student_history_returns_latest_first(self):
        recent_history = list(
            self.repository.get_recent_student_history(
                user_id=12,
                subject_id=3,
                topic_id=8,
                limit=2,
            )
        )

        self.assertEqual(len(recent_history), 2)
        self.assertEqual(
            [interaction.id for interaction in recent_history],
            [self.third_interaction.id, self.second_interaction.id],
        )

    def test_get_candidate_questions_returns_only_active_questions(self):
        candidate_questions = self.repository.get_candidate_questions(
            subject_id=3,
            topic_id=8,
        )

        candidate_ids = list(candidate_questions.values_list("id", flat=True))

        self.assertIn(self.question_easy.id, candidate_ids)
        self.assertIn(self.question_medium.id, candidate_ids)
        self.assertIn(self.question_hard.id, candidate_ids)
        self.assertNotIn(self.inactive_question.id, candidate_ids)

    def test_new_student_returns_empty_history_and_seen_questions(self):
        student_history = self.repository.get_student_history(
            user_id=99,
            subject_id=3,
            topic_id=8,
        )

        seen_question_ids = self.repository.get_seen_question_ids(
            user_id=99,
            subject_id=3,
            topic_id=8,
        )

        candidate_questions = self.repository.get_candidate_questions(
            subject_id=3,
            topic_id=8,
        )

        self.assertEqual(student_history.count(), 0)
        self.assertEqual(seen_question_ids, [])
        self.assertGreater(candidate_questions.count(), 0)

    def test_build_student_context_composes_correctly(self):
        student_context = self.repository.build_student_context(
            user_id=12,
            subject_id=3,
            topic_id=8,
        )

        self.assertEqual(student_context.history.count(), 3)
        self.assertEqual(student_context.recent_history.count(), 3)
        self.assertEqual(
            list(student_context.recent_history.values_list("id", flat=True)),
            [self.third_interaction.id, self.second_interaction.id, self.first_interaction.id],
        )
        self.assertEqual(len(student_context.seen_question_ids), 2)
        self.assertGreater(student_context.candidate_questions.count(), 0)
