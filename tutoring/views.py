import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from tutoring.serializers import RecommendationRequestSerializer
from tutoring.services.recommendation_engine import QuestionRecommendationEngine
from tutoring.serializers import AdaptiveFeedbackRequestSerializer
from tutoring.services.feedback_service import (
    FeedbackService,
    StudentNotFoundError as FeedbackStudentNotFoundError,
    QuestionNotFoundError,
)
from tutoring.services.student_sync_service import StudentSyncService
from tutoring.serializers import StudentSyncRequestSerializer

from tutoring.serializers import (
    AdaptiveExercisesRequestSerializer,
    AdaptiveExercisesResponseSerializer,
    CurriculumCatalogQuerySerializer,
    CurriculumCatalogResponseSerializer,
)
from tutoring.security.api_key_permission import HasValidApiKey
from tutoring.services.adaptive_exercise_service import (
    AdaptiveExerciseService,
    StudentNotFoundError as AdaptiveExerciseStudentNotFoundError,
)
from tutoring.services.curriculum_catalog_service import CurriculumCatalogService

logger = logging.getLogger(__name__)
INVALID_API_KEY_MESSAGE = "Invalid API key"

class AdaptiveExercisesView(APIView):
    permission_classes = [HasValidApiKey]

    def post(self, request):

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        logger.info(f"AdaptiveExercises request data: {request.data}")
        serializer = AdaptiveExercisesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"AdaptiveExercises validation errors: {serializer.errors}")
            serializer.is_valid(raise_exception=True)
        else:
            logger.info(f"AdaptiveExercises validation passed: {serializer.validated_data}")

        student_id = serializer.validated_data["studentId"]
        subject_id = serializer.validated_data["subjectId"]
        topic_id = serializer.validated_data["topicId"]
        count = serializer.validated_data["count"]

        service = AdaptiveExerciseService()

        try:
            exercises = service.generate_exercises(
                student_id=student_id,
                subject_id=subject_id,
                topic_id=topic_id,
                count=count,
            )

        except AdaptiveExerciseStudentNotFoundError:
            return Response(
                {
                    "error": "Studentul nu există în modulul AI. Sincronizați studentul înainte."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception:
            return Response(
                {
                    "error": "Serviciul de exerciții adaptive nu este disponibil"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_payload = {
            "exercises": exercises,
        }

        response_serializer = AdaptiveExercisesResponseSerializer(
            data=response_payload
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK,
        )

class RecommendQuestionView(APIView):
    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            validated_data = serializer.validated_data

            engine = QuestionRecommendationEngine()
            result = engine.recommend(
                user_id=validated_data["user_id"],
                subject_id=validated_data["subject_id"],
                topic_id=validated_data["topic_id"],
            )

            if result is None:
                return Response(
                    {"error": "No question could be recommended for the given topic."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "question_id": result.question_id,
                    "difficulty": result.difficulty,
                    "source": result.source,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Unexpected error while generating recommendation")
            return Response(
                {"error": "Internal server error while generating recommendation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class StudentSyncView(APIView):
    def post(self, request):

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        serializer = StudentSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_id = serializer.validated_data["requestId"]
        student_id = serializer.validated_data["studentId"]

        service = StudentSyncService()
        _, created = service.sync_student(student_id=student_id)

        message = ("Student registered in AI module with default topic levels."
            if created else
                "Student already exists. Missing topic levels were ensured.")
        
        return Response(
            {
                "requestId": request_id,
                "status": "ok",
                "message": message
            },
        )

class AdaptiveFeedbackView(APIView):
    def post(self, request):
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        serializer = AdaptiveFeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = FeedbackService()

        try:
            service.record_feedback(
                student_id=serializer.validated_data["studentId"],
                subject_id=serializer.validated_data["subjectId"],
                topic_id=serializer.validated_data["topicId"],
                results=serializer.validated_data["results"],
            )

        except FeedbackStudentNotFoundError:
            return Response({"ack": False}, status=status.HTTP_404_NOT_FOUND)

        except QuestionNotFoundError:
            return Response({"ack": False}, status=status.HTTP_404_NOT_FOUND)

        except Exception:
            logger.exception("Unexpected error while recording adaptive feedback")
            return Response(
                {"ack": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"ack": True}, status=status.HTTP_200_OK)


class CurriculumCatalogView(APIView):
    def get(self, request):
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        serializer = CurriculumCatalogQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        service = CurriculumCatalogService()
        catalog = service.list_catalog(
            grade=serializer.validated_data.get("grade"),
            subject_id=serializer.validated_data.get("subjectId"),
            topic_id=serializer.validated_data.get("topicId"),
        )

        response_serializer = CurriculumCatalogResponseSerializer(data=catalog)
        response_serializer.is_valid(raise_exception=True)

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK,
        )
