from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from tutoring.models import (
    Question,
    QuestionOption,
    QuestionCorrectOption,
    QuestionType,
)


class RecommendQuestionViewTests(APITestCase):
    def setUp(self):
        self.question = Question.objects.create(
            id=41,
            subject_id=3,
            topic_id=8,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Which planet is known as the Red Planet?",
            difficulty=0.4,
            is_active=True,
            times_answered=0,
            times_correct=0,
            avg_time_spent=0.0,
        )

        option_1 = QuestionOption.objects.create(
            id=201,
            question=self.question,
            text="Earth",
            display_order=1,
        )
        option_2 = QuestionOption.objects.create(
            id=202,
            question=self.question,
            text="Mars",
            display_order=2,
        )
        option_3 = QuestionOption.objects.create(
            id=203,
            question=self.question,
            text="Venus",
            display_order=3,
        )
        option_4 = QuestionOption.objects.create(
            id=204,
            question=self.question,
            text="Jupiter",
            display_order=4,
        )

        QuestionCorrectOption.objects.create(
            question=self.question,
            option=option_2,
        )

    def test_recommend_question_success(self):
        url = reverse("recommend-question")

        payload = {
            "user_id": 12,
            "subject_id": 3,
            "topic_id": 8,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("question_id", response.data)
        self.assertIn("difficulty", response.data)
        self.assertIn("source", response.data)

        self.assertEqual(response.data["question_id"], 41)
        self.assertEqual(response.data["source"], "selection")

    def test_missing_subject_id_returns_400(self):
        url = reverse("recommend-question")

        payload = {
            "user_id": 12,
            "topic_id": 8,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("subject_id", response.data)

    @patch("tutoring.views.QuestionRecommendationEngine")
    def test_no_recommendation_returns_404(self, mock_engine_class):
        mock_engine = mock_engine_class.return_value
        mock_engine.recommend.return_value = None

        url = reverse("recommend-question")

        payload = {
            "user_id": 12,
            "subject_id": 3,
            "topic_id": 8,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)