from django.test import TestCase
from tutoring.models import Question, StudentInteraction
from tutoring.repositories.student_data_repository import StudentDataRepository


class StudentDataRepositoryTests(TestCase):
    def setUp(self):
        self.repo = StudentDataRepository()

        self.q1 = Question.objects.create(subject_id=3, topic_id=8, content="Q1", difficulty_initial=0.2)
        self.q2 = Question.objects.create(subject_id=3, topic_id=8, content="Q2", difficulty_initial=0.5)
        self.q3 = Question.objects.create(subject_id=3, topic_id=8, content="Q3", difficulty_initial=0.8)
        self.q_inactive = Question.objects.create(subject_id=3, topic_id=8, content="Q4", is_active=False)

        # user 12 answered q1 twice and q2 once
        StudentInteraction.objects.create(user_id=12, question=self.q1, is_correct=True, time_spent=30.0)
        StudentInteraction.objects.create(user_id=12, question=self.q1, is_correct=False, time_spent=45.0)
        StudentInteraction.objects.create(user_id=12, question=self.q2, is_correct=True, time_spent=20.0)

    def test_get_student_history_returns_correct_interactions(self):
        history = self.repo.get_student_history(user_id=12, subject_id=3, topic_id=8)
        self.assertEqual(history.count(), 3)

    def test_get_seen_question_ids_returns_unique_ids(self):
        seen_ids = self.repo.get_seen_question_ids(user_id=12, subject_id=3, topic_id=8)
        self.assertEqual(len(seen_ids), len(set(seen_ids)))
        self.assertIn(self.q1.id, seen_ids)
        self.assertIn(self.q2.id, seen_ids)
        self.assertNotIn(self.q3.id, seen_ids)

    def test_get_candidate_questions_returns_only_active(self):
        candidates = self.repo.get_candidate_questions(subject_id=3, topic_id=8)
        ids = list(candidates.values_list("id", flat=True))
        self.assertIn(self.q1.id, ids)
        self.assertNotIn(self.q_inactive.id, ids)

    def test_new_student_returns_empty_history_and_seen(self):
        history = self.repo.get_student_history(user_id=99, subject_id=3, topic_id=8)
        seen_ids = self.repo.get_seen_question_ids(user_id=99, subject_id=3, topic_id=8)
        candidates = self.repo.get_candidate_questions(subject_id=3, topic_id=8)

        self.assertEqual(history.count(), 0)
        self.assertEqual(seen_ids, [])
        self.assertGreater(candidates.count(), 0)

    def test_build_student_context_composes_correctly(self):
        ctx = self.repo.build_student_context(user_id=12, subject_id=3, topic_id=8)
        self.assertEqual(ctx.history.count(), 3)
        self.assertEqual(len(ctx.seen_question_ids), 2)
        self.assertGreater(ctx.candidate_questions.count(), 0)
