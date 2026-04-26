import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from tutoring.serializers import RecommendationRequestSerializer
from tutoring.services.recommendation_engine import QuestionRecommendationEngine

from tutoring.services.student_sync_service import StudentSyncService
from tutoring.serializers import StudentSyncRequestSerializer

logger = logging.getLogger(__name__)

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
            raise PermissionDenied("Invalid API key")

        serializer = StudentSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requestId = serializer.validated_data["requestId"]
        studentId = serializer.validated_data["studentId"]

        service = StudentSyncService()
        student, created = service.sync_student(student_id = studentId)

        message = ("Student registered in AI module with default topic levels."
            if created else
                "Student already exists. Missing topic levels were ensured.")
        
        return Response(
            {
                "requestId": requestId,
                "status": "ok",
                "message": message
            },
        )