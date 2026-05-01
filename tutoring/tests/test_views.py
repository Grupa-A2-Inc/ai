from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, APITestCase

from tutoring.services.adaptive_exercise_service import (
    StudentNotFoundError as AdaptiveExerciseStudentNotFoundError,
)
from tutoring.services.feedback_service import (
    QuestionNotFoundError,
    StudentNotFoundError as FeedbackStudentNotFoundError,
)
from tutoring.views import (
    AdaptiveExercisesView,
    AdaptiveFeedbackView,
    RecommendQuestionView,
    StudentSyncView,
)


VALID_EXERCISE = {
    "exerciseId": "exercise-1",
    "text": "What is 2 + 2?",
    "type": "SINGLE_CHOICE",
    "answers": ["3", "4"],
    "correctAnswers": ["4"],
    "difficulty": 0.5,
}


def assert_invalid_api_key_is_rejected(view_class):
    request = SimpleNamespace(headers={"X-API-Key": "wrong-key"})

    with pytest.raises(PermissionDenied):
        view_class().post(request)


@override_settings(EXTERNAL_API_KEY="test-secret")
class ViewCoverageTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_adaptive_exercises_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(AdaptiveExercisesView)

    @patch("tutoring.views.AdaptiveExerciseService")
    def test_adaptive_exercises_returns_serialized_exercises(self, service_class):
        service = service_class.return_value
        service.generate_exercises.return_value = [VALID_EXERCISE]

        response = self.client.post(
            reverse("adaptive-exercises"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "count": 1,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"exercises": [VALID_EXERCISE]})
        service.generate_exercises.assert_called_once_with(
            student_id="student-1",
            subject_id=1,
            topic_id=2,
            count=1,
        )

    @patch("tutoring.views.AdaptiveExerciseService")
    def test_adaptive_exercises_returns_404_for_missing_student(self, service_class):
        service_class.return_value.generate_exercises.side_effect = (
            AdaptiveExerciseStudentNotFoundError()
        )

        response = self.client.post(
            reverse("adaptive-exercises"),
            {
                "studentId": "missing-student",
                "subjectId": 1,
                "topicId": 2,
                "count": 1,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["error"],
            "Studentul nu există în modulul AI. Sincronizați studentul înainte.",
        )

    @patch("tutoring.views.AdaptiveExerciseService")
    def test_adaptive_exercises_returns_503_for_unexpected_error(self, service_class):
        service_class.return_value.generate_exercises.side_effect = RuntimeError()

        response = self.client.post(
            reverse("adaptive-exercises"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "count": 1,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data,
            {"error": "Serviciul de exerciții adaptive nu este disponibil"},
        )

    @patch("tutoring.views.QuestionRecommendationEngine")
    def test_recommend_question_returns_recommendation(self, engine_class):
        engine_class.return_value.recommend.return_value = SimpleNamespace(
            question_id=12,
            difficulty=0.7,
            source="adaptive",
        )
        request = self.factory.post(
            "/recommend/",
            {"user_id": 1, "subject_id": 2, "topic_id": 3},
            format="json",
        )

        response = RecommendQuestionView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"question_id": 12, "difficulty": 0.7, "source": "adaptive"},
        )
        engine_class.return_value.recommend.assert_called_once_with(
            user_id=1,
            subject_id=2,
            topic_id=3,
        )

    @patch("tutoring.views.QuestionRecommendationEngine")
    def test_recommend_question_returns_404_when_no_result(self, engine_class):
        engine_class.return_value.recommend.return_value = None
        request = self.factory.post(
            "/recommend/",
            {"user_id": 1, "subject_id": 2, "topic_id": 3},
            format="json",
        )

        response = RecommendQuestionView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data,
            {"error": "No question could be recommended for the given topic."},
        )

    @patch("tutoring.views.QuestionRecommendationEngine")
    def test_recommend_question_returns_500_for_unexpected_error(self, engine_class):
        engine_class.return_value.recommend.side_effect = RuntimeError()
        request = self.factory.post(
            "/recommend/",
            {"user_id": 1, "subject_id": 2, "topic_id": 3},
            format="json",
        )

        response = RecommendQuestionView.as_view()(request)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {"error": "Internal server error while generating recommendation."},
        )

    def test_student_sync_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(StudentSyncView)

    @patch("tutoring.views.StudentSyncService")
    def test_student_sync_returns_created_message(self, service_class):
        service_class.return_value.sync_student.return_value = (Mock(), True)

        response = self.client.post(
            reverse("student-sync"),
            {"requestId": "request-1", "studentId": "student-1"},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "requestId": "request-1",
                "status": "ok",
                "message": (
                    "Student registered in AI module with default topic levels."
                ),
            },
        )
        service_class.return_value.sync_student.assert_called_once_with(
            student_id="student-1"
        )

    @patch("tutoring.views.StudentSyncService")
    def test_student_sync_returns_existing_student_message(self, service_class):
        service_class.return_value.sync_student.return_value = (Mock(), False)

        response = self.client.post(
            reverse("student-sync"),
            {"requestId": "request-1", "studentId": "student-1"},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["requestId"], "request-1")
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(
            response.data["message"],
            "Student already exists. Missing topic levels were ensured.",
        )

    def test_adaptive_feedback_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(AdaptiveFeedbackView)

    @patch("tutoring.views.FeedbackService")
    def test_adaptive_feedback_returns_ack_true(self, service_class):
        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "results": [
                    {"mlExerciseId": "exercise-1", "score": 1, "timeSpent": 30},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ack": True})
        service_class.return_value.record_feedback.assert_called_once_with(
            student_id="student-1",
            subject_id=1,
            topic_id=2,
            results=[
                {
                    "mlExerciseId": "exercise-1",
                    "score": 1.0,
                    "timeSpent": 30.0,
                }
            ],
        )

    @patch("tutoring.views.FeedbackService")
    def test_adaptive_feedback_returns_404_for_missing_student(self, service_class):
        service_class.return_value.record_feedback.side_effect = (
            FeedbackStudentNotFoundError()
        )

        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "missing-student",
                "subjectId": 1,
                "topicId": 2,
                "results": [
                    {"mlExerciseId": "exercise-1", "score": 1, "timeSpent": 30},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"ack": False})

    @patch("tutoring.views.FeedbackService")
    def test_adaptive_feedback_returns_404_for_missing_question(self, service_class):
        service_class.return_value.record_feedback.side_effect = QuestionNotFoundError()

        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "results": [
                    {"mlExerciseId": "missing-exercise", "score": 1, "timeSpent": 30},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"ack": False})

    @patch("tutoring.views.FeedbackService")
    def test_adaptive_feedback_returns_500_for_unexpected_error(self, service_class):
        service_class.return_value.record_feedback.side_effect = RuntimeError()

        response = self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "results": [
                    {"mlExerciseId": "exercise-1", "score": 1, "timeSpent": 30},
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"ack": False})
