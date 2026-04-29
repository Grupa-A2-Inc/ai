from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from tutoring.models import (
    StudentProfile,
    StudentTopicLevel,
    Question,
    QuestionType,
    QuestionOption,
    QuestionCorrectOption,
)


@override_settings(AI_API_KEY="test-secret")
class AdaptiveExercisesEndpointTests(APITestCase):
    def setUp(self):
        self.student = StudentProfile.objects.create(
            student_id="student-uuid-1",
            is_active=True,
        )

        StudentTopicLevel.objects.create(
            student=self.student,
            subject_id=2,
            topic_id=1102,
            mastery_score=0.5,
        )

        self.question_one = self._create_question(
            question_id=101,
            difficulty=0.5,
            content="Question 1",
        )

        self.question_two = self._create_question(
            question_id=102,
            difficulty=0.6,
            content="Question 2",
        )

    def _create_question(self, question_id: int, difficulty: float, content: str):
        question = Question.objects.create(
            id=question_id,
            subject_id=2,
            topic_id=1102,
            question_type=QuestionType.SINGLE_CHOICE,
            content=content,
            difficulty=difficulty,
            is_active=True,
        )

        option_one = QuestionOption.objects.create(
            question=question,
            text="Answer A",
            display_order=1,
        )

        QuestionOption.objects.create(
            question=question,
            text="Answer B",
            display_order=2,
        )

        QuestionCorrectOption.objects.create(
            question=question,
            option=option_one,
        )

        return question

    def test_adaptive_exercises_success(self):
        url = reverse("adaptive-exercises")

        payload = {
            "studentId": "student-uuid-1",
            "subjectId": 2,
            "topicId": 1102,
            "count": 1,
        }

        response = self.client.post(
            url,
            payload,
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("exercises", response.data)
        self.assertEqual(len(response.data["exercises"]), 1)

        exercise = response.data["exercises"][0]

        self.assertIn("exerciseId", exercise)
        self.assertIn("text", exercise)
        self.assertIn("type", exercise)
        self.assertIn("answers", exercise)
        self.assertIn("correctAnswers", exercise)
        self.assertIn("difficulty", exercise)

    def test_adaptive_exercises_default_count_is_five(self):
        url = reverse("adaptive-exercises")

        payload = {
            "studentId": "student-uuid-1",
            "subjectId": 2,
            "topicId": 1102,
        }

        response = self.client.post(
            url,
            payload,
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("exercises", response.data)

    def test_adaptive_exercises_returns_404_for_missing_student(self):
        url = reverse("adaptive-exercises")

        payload = {
            "studentId": "missing-student",
            "subjectId": 2,
            "topicId": 1102,
            "count": 1,
        }

        response = self.client.post(
            url,
            payload,
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)

    def test_adaptive_exercises_rejects_invalid_count(self):
        url = reverse("adaptive-exercises")

        payload = {
            "studentId": "student-uuid-1",
            "subjectId": 2,
            "topicId": 1102,
            "count": 0,
        }

        response = self.client.post(
            url,
            payload,
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 400)

    def test_adaptive_exercises_requires_api_key(self):
        url = reverse("adaptive-exercises")

        payload = {
            "studentId": "student-uuid-1",
            "subjectId": 2,
            "topicId": 1102,
            "count": 1,
        }

        response = self.client.post(
            url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 401)