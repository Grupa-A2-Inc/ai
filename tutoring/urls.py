from django.urls import path
from .views import RecommendQuestionView
from .views import StudentSyncView


urlpatterns = [
    path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
    path("api/students", StudentSyncView.as_view()),
]

