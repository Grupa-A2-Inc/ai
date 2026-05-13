from django.test import SimpleTestCase
from django.test import RequestFactory
from django.test import override_settings

from adaptive_ai.urls import health


class HealthEndpointTests(SimpleTestCase):
    def test_health_function_returns_up_status(self):
        request = RequestFactory().get("/health/")

        response = health(request)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "UP"})

    def test_health_allows_get(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "UP"})

    def test_health_rejects_unsafe_methods(self):
        response = self.client.post("/health/")

        self.assertEqual(response.status_code, 405)

    @override_settings(CORS_ALLOWED_ORIGINS=["https://adaptiveelearning.online"])
    def test_cors_preflight_allows_configured_origin(self):
        response = self.client.options(
            "/ai/api/v1/chat/customer-support",
            HTTP_ORIGIN="https://adaptiveelearning.online",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-api-key",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://adaptiveelearning.online",
        )
        self.assertIn("X-API-Key", response["Access-Control-Allow-Headers"])

    @override_settings(CORS_ALLOWED_ORIGINS=["https://adaptiveelearning.online"])
    def test_cors_preflight_rejects_unconfigured_origin(self):
        response = self.client.options(
            "/ai/api/v1/chat/customer-support",
            HTTP_ORIGIN="https://evil.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_cors_preflight_allows_default_vercel_frontend_origin(self):
        response = self.client.options(
            "/ai/api/v1/chat/customer-support",
            HTTP_ORIGIN="https://frontend-teal-five-57.vercel.app",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-api-key",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://frontend-teal-five-57.vercel.app",
        )
