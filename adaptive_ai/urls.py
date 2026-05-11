from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.views.decorators.http import require_GET

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from tutoring.views import GenerateQuestionsView

@require_GET
def health(request):
    return JsonResponse({"status": "UP"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('ai/', include('tutoring.urls')),

    # OpenAPI schema
    path('ai/api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path(
        'ai/api/v1/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    # Optional: ReDoc UI
    path(
        'ai/api/v1/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]
