from django.urls import path
from tutoring.views import RecommendQuestionView

urlpatterns = [
    path("recommend/", RecommendQuestionView.as_view(), name="recommend-question"),
]