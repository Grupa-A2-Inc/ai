from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from tutoring.models import (
    StudentProfile,
    StudentTopicLevel,
    StudentInteraction,
    Question,
    QuestionType,
)


@override_settings(EXTERNAL_API_KEY="test-secret")
class AdaptiveFeedbackEndpointTests(APITestCase):
    def setUp(self):
        self.student = StudentProfile.objects.create(
            student_id="student-uuid-1",
            is_active=True,
        )

        self.topic_level = StudentTopicLevel.objects.create(
            student=self.student,
            subject_id=2,
            topic_id=1102,
            mastery_score=0.5,
        )

        self.question_one = Question.objects.create(
            subject_id=2,
            topic_id=1102,
            ml_exercise_id="1",
            question_type=QuestionType.SINGLE_CHOICE,
            content="Exercise 1",
            difficulty=0.5,
            is_active=True,
        )

        self.question_two = Question.objects.create(
            subject_id=2,
            topic_id=1102,
            ml_exercise_id="2",
            question_type=QuestionType.SINGLE_CHOICE,
            content="Exercise 2",
            difficulty=0.6,
            is_active=True,
        )

        self.question_three = Question.objects.create(
            subject_id=2,
            topic_id=1102,
            ml_exercise_id="3",
            question_type=QuestionType.MULTIPLE_CHOICE,
            content="Exercise 3",
            difficulty=0.7,
            is_active=True,
        )

    def test_feedback_success_creates_student_interactions(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1, "timeSpent": 45},
                    {"mlExerciseId": "2", "score": 0, "timeSpent": 120},
                    {"mlExerciseId": "3", "score": 0.5, "timeSpent": 80},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ack"], True)

        self.assertEqual(StudentInteraction.objects.count(), 3)

        interaction_one = StudentInteraction.objects.get(ml_exercise_id="1")

        self.assertEqual(interaction_one.user_id, "student-uuid-1")
        self.assertEqual(interaction_one.question, self.question_one)
        self.assertEqual(interaction_one.score, 1)
        self.assertEqual(interaction_one.time_spent, 45)
        self.assertTrue(interaction_one.is_correct)

    def test_feedback_updates_question_statistics(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1, "timeSpent": 20},
                    {"mlExerciseId": "1", "score": 0, "timeSpent": 40},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)

        self.question_one.refresh_from_db()

        self.assertEqual(self.question_one.times_answered, 2)
        self.assertEqual(self.question_one.times_correct, 1)
        self.assertEqual(self.question_one.avg_time_spent, 30)

    def test_feedback_with_good_scores_increases_mastery(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1, "timeSpent": 30},
                    {"mlExerciseId": "2", "score": 1, "timeSpent": 35},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)

        self.topic_level.refresh_from_db()

        self.assertAlmostEqual(self.topic_level.mastery_score, 0.6)

    def test_feedback_with_bad_scores_decreases_mastery(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 0, "timeSpent": 90},
                    {"mlExerciseId": "2", "score": 0, "timeSpent": 110},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)

        self.topic_level.refresh_from_db()

        self.assertAlmostEqual(self.topic_level.mastery_score, 0.4)

    def test_feedback_returns_404_for_missing_student(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "missing-student",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1, "timeSpent": 45},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["ack"], False)

    def test_feedback_returns_404_for_missing_exercise(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {
                        "mlExerciseId": "missing-exercise",
                        "score": 1,
                        "timeSpent": 45,
                    },
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["ack"], False)

    def test_feedback_rejects_invalid_score(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1.5, "timeSpent": 45},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 400)

    def test_feedback_rejects_empty_results(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 400)

    def test_feedback_requires_api_key(self):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-uuid-1",
                "subjectId": 2,
                "topicId": 1102,
                "results": [
                    {"mlExerciseId": "1", "score": 1, "timeSpent": 45},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
