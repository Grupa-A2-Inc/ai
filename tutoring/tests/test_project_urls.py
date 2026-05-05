from django.test import SimpleTestCase
from django.test import RequestFactory

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
