from unittest.mock import patch
from rest_framework.test import APITestCase
from django.urls import reverse

class RecommendQuestionViewTests(APITestCase):
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