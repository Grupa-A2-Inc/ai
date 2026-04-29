from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView
from .views import AdaptiveFeedbackView
from tutoring.views import AdaptiveExercisesView

urlpatterns = [
    path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
    path("api/students", StudentSyncView.as_view(), name="student-sync"),
    path("api/adaptive/feedback",AdaptiveFeedbackView.as_view(), name="adaptive-feedback"),
    path("api/adaptive/exercises", AdaptiveExercisesView.as_view(), name="adaptive-exercises"),
    ]
