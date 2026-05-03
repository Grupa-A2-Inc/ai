from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def health(request):
    return JsonResponse({"status": "UP"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('ai/', include('tutoring.urls')),
]