from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView

from tutoring.views import AdaptiveExercisesView


urlpatterns = [
    path("api/students", StudentSyncView.as_view(), name="student-sync"),
    path("api/adaptive/exercises", AdaptiveExercisesView.as_view(), name="adaptive-exercises"),
    path("api/adaptive/feedback", AdaptiveFeedbackView.as_view(), name="adaptive-feedback"),
]

