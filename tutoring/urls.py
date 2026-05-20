from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView
from .views import AdaptiveFeedbackView
from tutoring.views import (
    AdaptiveExercisesView,
    AdaptiveExercisesJobCreateView,
    AdaptiveExercisesJobStatusView,
    CurriculumCatalogView,
    CustomerSupportChatView,
    GenerateQuestionsJobCreateView,
    GenerateQuestionsJobStatusView,
    GenerateQuestionsView,
)

urlpatterns = [
    path("api/v1/students", StudentSyncView.as_view(), name="student-sync"),
    path("api/v1/adaptive/feedback",AdaptiveFeedbackView.as_view(), name="adaptive-feedback"),
    path("api/v1/adaptive/exercises", AdaptiveExercisesView.as_view(), name="adaptive-exercises"),
    path("api/v1/adaptive/exercises/jobs", AdaptiveExercisesJobCreateView.as_view(), name="adaptive-exercises-job-create"),
    path("api/v1/adaptive/exercises/jobs/<uuid:job_id>", AdaptiveExercisesJobStatusView.as_view(), name="adaptive-exercises-job-status"),
    path("api/v1/catalog/curriculum", CurriculumCatalogView.as_view(), name="curriculum-catalog"),
    path("api/v1/chat/customer-support", CustomerSupportChatView.as_view(), name="customer-support-chat"),
    path("api/v1/generate/jobs", GenerateQuestionsJobCreateView.as_view(), name="generate-questions-job-create"),
    path("api/v1/generate/jobs/<uuid:job_id>", GenerateQuestionsJobStatusView.as_view(), name="generate-questions-job-status"),
    path('api/v1/generate', GenerateQuestionsView.as_view(), name="generate-questions"),
    ]
