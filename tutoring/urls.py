from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView
from .views import AdaptiveFeedbackView

urlpatterns = [
    path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
    path("api/students", StudentSyncView.as_view()),
path(
    "api/adaptive/feedback",
    AdaptiveFeedbackView.as_view(),
    name="adaptive-feedback",
),
]

