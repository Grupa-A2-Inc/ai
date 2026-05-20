from types import SimpleNamespace
from uuid import uuid4
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
from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationInvalidResponseError,
    LLMQuestionGenerationUnavailableError,
)
from tutoring.views import (
    AdaptiveExercisesView,
    AdaptiveExercisesJobCreateView,
    AdaptiveExercisesJobStatusView,
    AdaptiveFeedbackView,
    CurriculumCatalogView,
    CustomerSupportChatView,
    GenerateQuestionsView,
    GenerateQuestionsJobCreateView,
    GenerateQuestionsJobStatusView,
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


@override_settings(EXTERNAL_API_KEY="test-secret", AI_API_KEY="test-secret")
class ViewCoverageTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_openapi_schema_documents_customer_support_chat(self):
        response = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "/ai/api/v1/chat/customer-support",
            response.data["paths"],
        )
        operation = response.data["paths"][
            "/ai/api/v1/chat/customer-support"
        ]["post"]
        self.assertEqual(operation["operationId"], "customerSupportChat")
        self.assertEqual(operation["tags"], ["Chatbots"])

    def test_openapi_schema_documents_async_generation_jobs(self):
        response = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("/ai/api/v1/generate/jobs", response.data["paths"])
        self.assertIn(
            "/ai/api/v1/generate/jobs/{job_id}",
            response.data["paths"],
        )

        create_operation = response.data["paths"][
            "/ai/api/v1/generate/jobs"
        ]["post"]
        status_operation = response.data["paths"][
            "/ai/api/v1/generate/jobs/{job_id}"
        ]["get"]

        self.assertEqual(
            create_operation["operationId"],
            "createQuestionGenerationJob",
        )
        self.assertEqual(
            status_operation["operationId"],
            "getQuestionGenerationJob",
        )
        self.assertEqual(create_operation["tags"], ["LLM Generation"])
        self.assertEqual(status_operation["tags"], ["LLM Generation"])

    def test_openapi_schema_documents_async_adaptive_exercise_jobs(self):
        response = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("/ai/api/v1/adaptive/exercises/jobs", response.data["paths"])
        self.assertIn(
            "/ai/api/v1/adaptive/exercises/jobs/{job_id}",
            response.data["paths"],
        )

        create_operation = response.data["paths"][
            "/ai/api/v1/adaptive/exercises/jobs"
        ]["post"]
        status_operation = response.data["paths"][
            "/ai/api/v1/adaptive/exercises/jobs/{job_id}"
        ]["get"]

        self.assertEqual(
            create_operation["operationId"],
            "createAdaptiveExercisesJob",
        )
        self.assertEqual(
            status_operation["operationId"],
            "getAdaptiveExercisesJob",
        )
        self.assertEqual(create_operation["tags"], ["Adaptive Learning"])
        self.assertEqual(status_operation["tags"], ["Adaptive Learning"])

    def test_adaptive_exercises_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(AdaptiveExercisesView)

    def test_adaptive_exercises_job_create_rejects_invalid_api_key(self):
        response = self.client.post(
            reverse("adaptive-exercises-job-create"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "count": 1,
            },
            format="json",
            HTTP_X_API_KEY="wrong-key",
        )

        self.assertEqual(response.status_code, 403)

    @patch("tutoring.views.AdaptiveExerciseGenerationJobService")
    def test_adaptive_exercises_job_create_returns_job_id(self, service_class):
        job_id = uuid4()
        service_class.return_value.create_job.return_value = SimpleNamespace(
            id=job_id,
            status="PENDING",
        )

        response = self.client.post(
            reverse("adaptive-exercises-job-create"),
            {
                "studentId": "student-1",
                "subjectId": 1,
                "topicId": 2,
                "count": 12,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data, {"jobId": str(job_id), "status": "PENDING"})
        service_class.return_value.create_job.assert_called_once_with(
            student_id="student-1",
            subject_id=1,
            topic_id=2,
            count=12,
        )

    @patch("tutoring.views.AdaptiveExerciseGenerationJobService")
    def test_adaptive_exercises_job_status_returns_done_exercises(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = SimpleNamespace(
            id=job_id,
            status="DONE",
            result={"exercises": [VALID_EXERCISE]},
            error="",
        )

        response = self.client.get(
            reverse("adaptive-exercises-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "jobId": str(job_id),
                "status": "DONE",
                "exercises": [VALID_EXERCISE],
            },
        )

    @patch("tutoring.views.AdaptiveExerciseGenerationJobService")
    def test_adaptive_exercises_job_status_returns_failed_error(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = SimpleNamespace(
            id=job_id,
            status="FAILED",
            result=None,
            error="Studentul nu există.",
        )

        response = self.client.get(
            reverse("adaptive-exercises-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "jobId": str(job_id),
                "status": "FAILED",
                "error": "Studentul nu există.",
            },
        )

    @patch("tutoring.views.AdaptiveExerciseGenerationJobService")
    def test_adaptive_exercises_job_status_returns_404_when_missing(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = None

        response = self.client.get(
            reverse("adaptive-exercises-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data,
            {"error": "Jobul de exerciții adaptive nu există."},
        )

    def test_customer_support_chat_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(CustomerSupportChatView)

    @override_settings(EXTERNAL_API_KEY="external-secret", AI_API_KEY="ai-secret")
    @patch("tutoring.views.CustomerSupportChatService")
    def test_customer_support_chat_uses_ai_api_key(self, service_class):
        service_class.return_value.answer.return_value = "Răspuns suport."

        response = self.client.post(
            reverse("customer-support-chat"),
            {"message": "Am nevoie de ajutor."},
            format="json",
            HTTP_X_API_KEY="ai-secret",
        )

        self.assertEqual(response.status_code, 200)

    @patch("tutoring.views.CustomerSupportChatService")
    def test_customer_support_chat_returns_answer(self, service_class):
        service = service_class.return_value
        service.answer.return_value = (
            "Verifică secțiunea de progres din dashboard și reîncarcă pagina."
        )

        response = self.client.post(
            reverse("customer-support-chat"),
            {
                "message": "Nu îmi apare progresul.",
                "history": [
                    {"role": "user", "content": "Unde văd progresul meu?"},
                    {"role": "assistant", "content": "În pagina de profil."},
                ],
                "context": {"page": "dashboard", "userType": "student"},
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "answer": "Verifică secțiunea de progres din dashboard și reîncarcă pagina.",
                "chatbot": "customer_support",
            },
        )
        service.answer.assert_called_once_with(
            message="Nu îmi apare progresul.",
            history=[
                {"role": "user", "content": "Unde văd progresul meu?"},
                {"role": "assistant", "content": "În pagina de profil."},
            ],
            context={"page": "dashboard", "userType": "student"},
        )

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

    def test_curriculum_catalog_rejects_invalid_api_key_in_view(self):
        request = SimpleNamespace(headers={"X-API-Key": "wrong-key"})

        with pytest.raises(PermissionDenied):
            CurriculumCatalogView().get(request)

    def test_curriculum_catalog_returns_filtered_subjects_and_topics(self):
        response = self.client.get(
            reverse("curriculum-catalog"),
            {"grade": 9, "subjectId": 2},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["subjects"],
            [{"subjectId": 2, "subjectName": "Matematică"}],
        )
        self.assertEqual(
            response.data["topics"],
            [
                {
                    "topicId": 1101,
                    "subjectId": 2,
                    "subjectName": "Matematică",
                    "grade": 9,
                    "topicName": "Mulțimi de numere și operații",
                },
                {
                    "topicId": 1102,
                    "subjectId": 2,
                    "subjectName": "Matematică",
                    "grade": 9,
                    "topicName": "Ecuații și inecuații",
                },
                {
                    "topicId": 1103,
                    "subjectId": 2,
                    "subjectName": "Matematică",
                    "grade": 9,
                    "topicName": "Funcții și reprezentare grafică",
                },
                {
                    "topicId": 1104,
                    "subjectId": 2,
                    "subjectName": "Matematică",
                    "grade": 9,
                    "topicName": "Geometrie plană și relații metrice",
                },
            ],
        )

    def test_curriculum_catalog_can_resolve_single_topic_name(self):
        response = self.client.get(
            reverse("curriculum-catalog"),
            {"topicId": 1102},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["subjects"], [
            {"subjectId": 2, "subjectName": "Matematică"}
        ])
        self.assertEqual(response.data["topics"], [
            {
                "topicId": 1102,
                "subjectId": 2,
                "subjectName": "Matematică",
                "grade": 9,
                "topicName": "Ecuații și inecuații",
            }
        ])

    def test_curriculum_catalog_validates_query_params(self):
        response = self.client.get(
            reverse("curriculum-catalog"),
            {"grade": 0},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 400)

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

    def test_generate_questions_rejects_invalid_api_key_in_view(self):
        assert_invalid_api_key_is_rejected(GenerateQuestionsView)

    def test_generate_questions_job_create_rejects_invalid_api_key(self):
        response = self.client.post(
            reverse("generate-questions-job-create"),
            {"content": "Lesson", "count": 1},
            format="json",
            HTTP_X_API_KEY="wrong-key",
        )

        self.assertEqual(response.status_code, 403)

    @patch("tutoring.views.QuestionGenerationJobService")
    def test_generate_questions_job_create_returns_job_id(self, service_class):
        job_id = uuid4()
        service_class.return_value.create_job.return_value = SimpleNamespace(
            id=job_id,
            status="PENDING",
        )

        response = self.client.post(
            reverse("generate-questions-job-create"),
            {"content": "Lesson", "count": 3},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data,
            {"jobId": str(job_id), "status": "PENDING"},
        )
        service_class.return_value.create_job.assert_called_once_with(
            content="Lesson",
            count=3,
        )

    @patch("tutoring.views.QuestionGenerationJobService")
    def test_generate_questions_job_status_returns_running(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = SimpleNamespace(
            id=job_id,
            status="RUNNING",
            result=None,
            error="",
        )

        response = self.client.get(
            reverse("generate-questions-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"jobId": str(job_id), "status": "RUNNING"},
        )

    @patch("tutoring.views.QuestionGenerationJobService")
    def test_generate_questions_job_status_returns_done_questions(self, service_class):
        job_id = uuid4()
        generated_question = {
            "text": "Question?",
            "type": "SINGLE_CHOICE",
            "answers": ["A", "B", "C", "D"],
            "correctAnswers": ["A"],
            "difficulty": 0.5,
        }
        service_class.return_value.get_job.return_value = SimpleNamespace(
            id=job_id,
            status="DONE",
            result={"questions": [generated_question]},
            error="",
        )

        response = self.client.get(
            reverse("generate-questions-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "jobId": str(job_id),
                "status": "DONE",
                "questions": [generated_question],
            },
        )

    @patch("tutoring.views.QuestionGenerationJobService")
    def test_generate_questions_job_status_returns_failed_error(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = SimpleNamespace(
            id=job_id,
            status="FAILED",
            result=None,
            error="LLM failed.",
        )

        response = self.client.get(
            reverse("generate-questions-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "jobId": str(job_id),
                "status": "FAILED",
                "error": "LLM failed.",
            },
        )

    @patch("tutoring.views.QuestionGenerationJobService")
    def test_generate_questions_job_status_returns_404_when_missing(self, service_class):
        job_id = uuid4()
        service_class.return_value.get_job.return_value = None

        response = self.client.get(
            reverse("generate-questions-job-status", kwargs={"job_id": job_id}),
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": "Jobul de generare nu există."})

    @patch("tutoring.views.LLMQuestionGenerationService")
    def test_generate_questions_returns_generated_questions(self, service_class):
        generated_question = {
            "text": "Question?",
            "type": "SINGLE_CHOICE",
            "answers": ["A", "B", "C", "D"],
            "correctAnswers": ["A"],
            "difficulty": 0.5,
        }
        service_class.return_value.generate.return_value = [generated_question]

        response = self.client.post(
            reverse("generate-questions"),
            {"content": "Lesson", "count": 1},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"questions": [generated_question]})
        service_class.return_value.generate.assert_called_once_with(
            content="Lesson",
            count=1,
        )

    @patch("tutoring.views.LLMQuestionGenerationService")
    def test_generate_questions_returns_503_for_unavailable_llm(self, service_class):
        service_class.return_value.generate.side_effect = (
            LLMQuestionGenerationUnavailableError()
        )

        response = self.client.post(
            reverse("generate-questions"),
            {"content": "Lesson", "count": 1},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data,
            {"error": "Serviciul LLM nu este disponibil."},
        )

    @patch("tutoring.views.LLMQuestionGenerationService")
    def test_generate_questions_returns_502_for_invalid_llm_response(self, service_class):
        service_class.return_value.generate.side_effect = (
            LLMQuestionGenerationInvalidResponseError()
        )

        response = self.client.post(
            reverse("generate-questions"),
            {"content": "Lesson", "count": 1},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.data,
            {"error": "LLM-ul a returnat un răspuns invalid."},
        )

    @patch("tutoring.views.LLMQuestionGenerationService")
    def test_generate_questions_returns_503_for_unexpected_error(self, service_class):
        service_class.return_value.generate.side_effect = RuntimeError()

        response = self.client.post(
            reverse("generate-questions"),
            {"content": "Lesson", "count": 1},
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data,
            {"error": "Serviciul de generare întrebări nu este disponibil."},
        )
