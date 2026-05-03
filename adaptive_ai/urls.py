from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def health(request):
    return JsonResponse({"status": "UP"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('', include('tutoring.urls')),
    path('ai/', include('tutoring.urls')),

    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    # Optional: ReDoc UI
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]
