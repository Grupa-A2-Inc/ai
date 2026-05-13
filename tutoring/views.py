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

from tutoring.serializers import RecommendationRequestSerializer
from tutoring.serializers import RecommendationResponseSerializer
from tutoring.services.recommendation_engine import QuestionRecommendationEngine
from tutoring.serializers import AdaptiveFeedbackRequestSerializer
from tutoring.serializers import (
    GenerateQuestionsRequestSerializer,
    GenerateQuestionsResponseSerializer,
    CustomerSupportChatRequestSerializer,
    CustomerSupportChatResponseSerializer,
)
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
from tutoring.services.customer_support_chat_service import (
    CustomerSupportChatInvalidResponseError,
    CustomerSupportChatService,
    CustomerSupportChatUnavailableError,
)
from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationInvalidResponseError,
    LLMQuestionGenerationService,
    LLMQuestionGenerationUnavailableError,
)

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


class CustomerSupportChatView(APIView):
    permission_classes = [HasValidApiKey]

    @extend_schema(
        operation_id="customerSupportChat",
        tags=["Chatbots"],
        summary="Răspunde la întrebări de customer support",
        description=(
            "Primește mesajul curent al utilizatorului, istoricul conversației și contextul paginii curente. "
            "Răspunde ca un chatbot de customer support pentru platformă, folosind LLM-ul local configurat."
        ),
        parameters=[API_KEY_HEADER],
        request=CustomerSupportChatRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=CustomerSupportChatResponseSerializer,
                description="Răspuns generat cu succes.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            403: OpenApiResponse(description="X-API-Key lipsă sau invalid."),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="LLM-ul a returnat un răspuns invalid sau gol.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Serviciul de chat nu este disponibil.",
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="LLM-ul a returnat un răspuns invalid sau gol.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Serviciul de chat nu este disponibil.",
            ),
        },
        examples=[
            OpenApiExample(
                "Cerere customer support",
                value={
                    "message": "Nu îmi apare progresul la matematică.",
                    "history": [
                        {
                            "role": "user",
                            "content": "Unde văd progresul meu?",
                        },
                        {
                            "role": "assistant",
                            "content": (
                                "Îl poți vedea în pagina de profil sau "
                                "în secțiunea de progres."
                            ),
                        },
                    ],
                    "context": {
                        "page": "student-dashboard",
                        "userType": "student",
                    },
                },
                request_only=True,
            ),
            OpenApiExample(
                "Răspuns customer support",
                value={
                    "answer": (
                        "Verifică secțiunea de progres din dashboard. Dacă nu vezi datele, "
                        "încearcă să reîncarci pagina sau contactează suportul pentru detalii."
                    ),
                    "chatbot": "customer_support",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        serializer = CustomerSupportChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = CustomerSupportChatService()

        try:
            answer = service.answer(
                message=serializer.validated_data["message"],
                history=serializer.validated_data.get("history", []),
                context=serializer.validated_data.get("context", {}),
            )
        except CustomerSupportChatUnavailableError:
            return Response(
                {"error": "Serviciul de chat nu este disponibil."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except CustomerSupportChatInvalidResponseError:
            return Response(
                {"error": "LLM-ul a returnat un răspuns invalid sau gol."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_serializer = CustomerSupportChatResponseSerializer(
            data={"answer": answer, "chatbot": "customer_support"}
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class GenerateQuestionsView(APIView):
    permission_classes = [HasValidApiKey]

    @extend_schema(
        operation_id="generateQuestions",
        tags=["LLM Generation"],
        summary="Generează întrebări dintr-o lecție",
        description=(
            "Primește conținutul complet al unei lecții și numărul de întrebări "
            "care trebuie generate. Serviciul construiește promptul pentru LLM-ul local, "
            "apelează LLM-ul, parsează JSON-ul rezultat și întoarce întrebările "
            "validate în formatul standard."
        ),
        parameters=[API_KEY_HEADER],
        request=GenerateQuestionsRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=GenerateQuestionsResponseSerializer,
                description="Întrebări generate cu succes.",
            ),
            400: OpenApiResponse(description="Request invalid."),
            403: OpenApiResponse(description="X-Api-Key lipsă sau invalid."),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="LLM-ul a returnat un răspuns invalid.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="LLM-ul nu este disponibil.",
            ),
        },
        examples=[
            OpenApiExample(
                "Cerere generare întrebări",
                value={
                    "content": "Lecție despre ecuații de gradul al doilea...",
                    "count": 5,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Răspuns generare întrebări",
                value={
                    "questions": [
                        {
                            "text": "Care este forma generală a ecuației de gradul al doilea?",
                            "type": "SINGLE_CHOICE",
                            "answers": [
                                "ax² + bx + c = 0",
                                "ax + b = 0",
                                "a/x + b = 0",
                                "x + y = 0",
                            ],
                            "correctAnswers": ["ax² + bx + c = 0"],
                            "difficulty": 0.4,
                        }
                    ]
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        api_key = request.headers.get("X-Api-Key")
        if api_key != settings.EXTERNAL_API_KEY:
            raise PermissionDenied(INVALID_API_KEY_MESSAGE)

        serializer = GenerateQuestionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = LLMQuestionGenerationService()

        try:
            questions = service.generate(
                content=serializer.validated_data["content"],
                count=serializer.validated_data["count"],
            )
        except LLMQuestionGenerationUnavailableError:
            return Response(
                {"error": "Serviciul LLM nu este disponibil."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except LLMQuestionGenerationInvalidResponseError:
            return Response(
                {"error": "LLM-ul a returnat un răspuns invalid."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            logger.exception("Unexpected error while generating questions")
            return Response(
                {"error": "Serviciul de generare întrebări nu este disponibil."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_serializer = GenerateQuestionsResponseSerializer(
            data={"questions": questions}
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK,
        )
