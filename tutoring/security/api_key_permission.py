from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated


class HasValidApiKey(BasePermission):
    message = "Invalid API key"

    def has_permission(self, request, view):
        provided_key = request.headers.get("X-API-Key")
        expected_key = getattr(
            settings,
            "EXTERNAL_API_KEY",
            getattr(settings, "AI_API_KEY", ""),
        ) or getattr(settings, "AI_API_KEY", "")

        if provided_key and expected_key and provided_key == expected_key:
            return True

        raise NotAuthenticated(self.message)
