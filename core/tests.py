"""Shared helpers for the API tests."""
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

User = get_user_model()
PASSWORD = "StrongPassword123"


class AuthenticatedAPITestCase(APITestCase):
    """Creates two users; ``self.client`` is authenticated as ``self.user``."""

    def setUp(self):
        self.user = User.objects.create_user("john@example.com", "John", PASSWORD)
        self.other_user = User.objects.create_user("jane@example.com", "Jane", PASSWORD)
        self.client = self.client_for(self.user)
        self.other_client = self.client_for(self.other_user)

    def client_for(self, user):
        client = APIClient()
        response = client.post(
            "/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json"
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client
