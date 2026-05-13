import logging
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from datetime import datetime

from tutoring.serializers import RecommendationRequestSerializer
from tutoring.serializers import RecommendationResponseSerializer
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
    ChatSupportRequestSerializer,
    ChatSupportResponseSerializer,
)
from tutoring.security.api_key_permission import HasValidApiKey
from tutoring.services.adaptive_exercise_service import (
    AdaptiveExerciseService,
    StudentNotFoundError as AdaptiveExerciseStudentNotFoundError,
)
from tutoring.services.curriculum_catalog_service import CurriculumCatalogService
from tutoring.services.chat_support_service import ChatSupportService, ChatServiceError

logger = logging.getLogger(__name__)
INVALID_API_KEY_MESSAGE = "Invalid API key"

API_KEY_HEADER = OpenApiParameter(
    name="X-API-Key",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Cheia de acces configurată în modulul AI pentru apelurile backend-to-backend.",
)

ErrorResponseSerializer = inline_serializer(
    name="ErrorResponse",
    fields={"error": serializers.CharField()},
)

AckResponseSerializer = inline_serializer(
    name="AckResponse",
    fields={"ack": serializers.BooleanField()},
)

StudentSyncResponseSerializer = inline_serializer(
    name="StudentSyncResponse",
    fields={
        "requestId": serializers.CharField(),
        "status": serializers.CharField(),
        "message": serializers.CharField(),
    },
)

class AdaptiveExercisesView(APIView):
    permission_classes = [HasValidApiKey]

    @extend_schema(
        operation_id="generateAdaptiveExercises",
        tags=["Adaptive Learning"],
        summary="Generează exerciții adaptive pentru un elev",
        description=(
            "Primește elevul, materia și topicul selectat de aplicație și întoarce "
            "un set de exerciții calibrate pe nivelul estimat al elevului. Endpointul "
            "folosește istoricul elevului și banca de întrebări disponibilă pentru "
            "topic; dacă elevul nu există în modulul AI, trebuie apelată mai întâi "
            "sincronizarea elevului."
        ),
        parameters=[API_KEY_HEADER],
        request=AdaptiveExercisesRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=AdaptiveExercisesResponseSerializer,
                description="Exerciții generate cu succes.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            403: OpenApiResponse(description="X-API-Key lipsă sau invalid."),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Elevul nu este sincronizat în modulul AI.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Serviciul de exerciții adaptive nu este disponibil.",
            ),
        },
        examples=[
            OpenApiExample(
                "Cerere exerciții adaptive",
                value={
                    "studentId": "student-uuid-1",
                    "subjectId": 2,
                    "topicId": 1102,
                    "count": 5,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Răspuns exerciții adaptive",
                value={
                    "exercises": [
                        {
                            "exerciseId": "42",
                            "text": "Rezolvă ecuația 2x + 4 = 10.",
                            "type": "SINGLE_CHOICE",
                            "answers": ["x = 2", "x = 3", "x = 4"],
                            "correctAnswers": ["x = 3"],
                            "difficulty": 0.5,
                        }
                    ]
                },
                response_only=True,
            ),
        ],
    )
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
    @extend_schema(
        operation_id="recommendQuestion",
        tags=["Internal Recommendation"],
        summary="Recomandă următoarea întrebare pentru un topic",
        description=(
            "Endpoint intern istoric pentru recomandarea unei singure întrebări. "
            "Primește identificatorii elevului, materiei și topicului, apoi returnează "
            "întrebarea recomandată împreună cu dificultatea estimată și sursa deciziei."
        ),
        request=RecommendationRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=RecommendationResponseSerializer,
                description="Întrebare recomandată cu succes.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            404: OpenApiResponse(description="Nu există întrebare recomandabilă pentru topic."),
            500: OpenApiResponse(description="Eroare internă în motorul de recomandare."),
        },
    )
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
    @extend_schema(
        operation_id="syncStudent",
        tags=["Students"],
        summary="Sincronizează un elev în modulul AI",
        description=(
            "Creează profilul elevului în modulul AI dacă nu există deja și asigură "
            "niveluri implicite de mastery pentru topicurile disponibile. Endpointul "
            "este idempotent: apelurile repetate pentru același student nu dublează "
            "datele existente."
        ),
        parameters=[API_KEY_HEADER],
        request=StudentSyncRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=StudentSyncResponseSerializer,
                description="Elev sincronizat sau deja existent.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            403: OpenApiResponse(description="X-API-Key lipsă sau invalid."),
        },
        examples=[
            OpenApiExample(
                "Cerere sincronizare elev",
                value={"requestId": "request-1", "studentId": "student-uuid-1"},
                request_only=True,
            ),
            OpenApiExample(
                "Răspuns sincronizare elev",
                value={
                    "requestId": "request-1",
                    "status": "ok",
                    "message": "Student registered in AI module with default topic levels.",
                },
                response_only=True,
            ),
        ],
    )
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
    @extend_schema(
        operation_id="recordAdaptiveFeedback",
        tags=["Adaptive Learning"],
        summary="Înregistrează rezultatele exercițiilor adaptive",
        description=(
            "Primește rezultatele obținute de elev pentru exercițiile returnate anterior "
            "și actualizează istoricul interacțiunilor, statisticile întrebărilor și "
            "nivelul de mastery al elevului pe topic. Fiecare rezultat trebuie să "
            "referențieze un `mlExerciseId` valid pentru materia și topicul trimise."
        ),
        parameters=[API_KEY_HEADER],
        request=AdaptiveFeedbackRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=AckResponseSerializer,
                description="Feedback înregistrat cu succes.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            403: OpenApiResponse(description="X-API-Key lipsă sau invalid."),
            404: OpenApiResponse(
                response=AckResponseSerializer,
                description="Elevul sau exercițiul nu există.",
            ),
            500: OpenApiResponse(
                response=AckResponseSerializer,
                description="Eroare internă la înregistrarea feedbackului.",
            ),
        },
        examples=[
            OpenApiExample(
                "Cerere feedback",
                value={
                    "studentId": "student-uuid-1",
                    "subjectId": 2,
                    "topicId": 1102,
                    "results": [
                        {
                            "mlExerciseId": "42",
                            "score": 1.0,
                            "timeSpent": 35.5,
                        }
                    ],
                },
                request_only=True,
            ),
            OpenApiExample(
                "Răspuns feedback",
                value={"ack": True},
                response_only=True,
            ),
        ],
    )
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
    @extend_schema(
        operation_id="getCurriculumCatalog",
        tags=["Curriculum Catalog"],
        summary="Returnează catalogul de materii și topicuri",
        description=(
            "Expune către backend catalogul curricular folosit de modulul AI: "
            "`subjectId`, numele materiei, `topicId`, numele topicului și clasa. "
            "Fără filtre, endpointul returnează toate materiile și toate topicurile "
            "cunoscute. Filtrele pot fi combinate pentru a restrânge rezultatele după "
            "clasă, materie sau topic."
        ),
        parameters=[
            API_KEY_HEADER,
            OpenApiParameter(
                name="grade",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Clasa pentru care se returnează topicurile, de exemplu `9`.",
            ),
            OpenApiParameter(
                name="subjectId",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Materia pentru care se returnează topicurile, de exemplu `2` pentru Matematică.",
            ),
            OpenApiParameter(
                name="topicId",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Topicul exact care trebuie rezolvat la nume și clasă, de exemplu `1102`.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=CurriculumCatalogResponseSerializer,
                description="Catalog curricular returnat cu succes.",
            ),
            400: OpenApiResponse(description="Filtre invalide."),
            403: OpenApiResponse(description="X-API-Key lipsă sau invalid."),
        },
        examples=[
            OpenApiExample(
                "Răspuns catalog filtrat",
                value={
                    "subjects": [
                        {"subjectId": 2, "subjectName": "Matematică"}
                    ],
                    "topics": [
                        {
                            "topicId": 1102,
                            "subjectId": 2,
                            "subjectName": "Matematică",
                            "grade": 9,
                            "topicName": "Ecuații și inecuații",
                        }
                    ],
                },
                response_only=True,
            ),
        ],
    )
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


class ChatSupportView(APIView):
    """View for handling chat support requests via Ollama LLM."""
    
    permission_classes = []  # Allow public access to chat support
    
    @extend_schema(
        operation_id="chatSupport",
        tags=["Chat Support"],
        summary="Chat support endpoint powered by Ollama LLM",
        description=(
            "Endpoint for student support chat. Uses Ollama with qwen2.5:3b model "
            "to provide helpful responses to student questions about learning topics."
        ),
        request=ChatSupportRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=ChatSupportResponseSerializer,
                description="Chat response received successfully.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            503: OpenApiResponse(description="Chat service temporarily unavailable."),
        },
        examples=[
            OpenApiExample(
                "Chat request",
                value={
                    "message": "How do I solve quadratic equations?",
                    "studentId": "student-123",
                    "topicId": 5,
                    "context": "Currently studying algebra",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Chat response",
                value={
                    "response": "To solve quadratic equations, you can use the quadratic formula...",
                    "timestamp": "2024-05-13T14:30:00Z",
                    "model": "qwen2.5:3b",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Handle chat support POST requests."""
        serializer = ChatSupportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.validated_data["message"]
        student_id = serializer.validated_data.get("studentId")
        topic_id = serializer.validated_data.get("topicId")
        context = serializer.validated_data.get("context")
        language = serializer.validated_data.get("language", "en")
        
        # Build additional context if student/topic info is provided
        full_context = self._build_context(student_id, topic_id, context)
        
        try:
            service = ChatSupportService()
            response_text = service.chat(message=message, context=full_context, language=language)
            
            response_data = {
                "response": response_text,
                "timestamp": datetime.now().isoformat() + "Z",
                "model": service.model_name,
            }
            
            response_serializer = ChatSupportResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK,
            )
            
        except ChatServiceError as e:
            logger.warning(f"Chat service error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"Unexpected error in chat support: {e}")
            return Response(
                {"error": "An unexpected error occurred in the chat service."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
    
    def _build_context(self, student_id: str = None, topic_id: int = None, context: str = None) -> str:
        """Build context information for the chat service."""
        parts = []
        
        if student_id:
            parts.append(f"Student ID: {student_id}")
        
        if topic_id:
            parts.append(f"Topic ID: {topic_id}")
        
        if context:
            parts.append(f"Context: {context}")
        
        return " | ".join(parts) if parts else None
