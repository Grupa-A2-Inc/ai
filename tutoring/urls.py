from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView
from .views import AdaptiveFeedbackView
from tutoring.views import AdaptiveExercisesView, CurriculumCatalogView, ChatSupportView

urlpatterns = [
   # path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
    path("api/v1/students", StudentSyncView.as_view(), name="student-sync"),
    path("api/v1/adaptive/feedback",AdaptiveFeedbackView.as_view(), name="adaptive-feedback"),
    path("api/v1/adaptive/exercises", AdaptiveExercisesView.as_view(), name="adaptive-exercises"),
    path("api/v1/catalog/curriculum", CurriculumCatalogView.as_view(), name="curriculum-catalog"),
    path("api/v1/support/chat", ChatSupportView.as_view(), name="chat-support"),
    ]
