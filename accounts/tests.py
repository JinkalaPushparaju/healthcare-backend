from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"


class RegisterTests(APITestCase):
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "StrongPassword123",
    }

    def test_register_success(self):
        response = self.client.post(REGISTER_URL, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered successfully")
        self.assertEqual(response.data["user"]["email"], "john@example.com")
        self.assertNotIn("password", response.data["user"])
        user = User.objects.get(email="john@example.com")
        self.assertNotEqual(user.password, self.payload["password"])
        self.assertTrue(user.check_password(self.payload["password"]))

    def test_register_duplicate_email(self):
        self.client.post(REGISTER_URL, self.payload, format="json")
        response = self.client.post(
            REGISTER_URL, {**self.payload, "email": "JOHN@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["email"][0], "A user with this email already exists."
        )

    def test_register_invalid_email(self):
        response = self.client.post(
            REGISTER_URL, {**self.payload, "email": "not-an-email"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_weak_password(self):
        response = self.client.post(
            REGISTER_URL, {**self.payload, "password": "12345"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_missing_fields(self):
        response = self.client.post(REGISTER_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("name", "email", "password"):
            self.assertIn(field, response.data)


class LoginTests(APITestCase):
    def setUp(self):
        User.objects.create_user("john@example.com", "John", "StrongPassword123")

    def test_login_success(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "john@example.com", "password": "StrongPassword123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "john@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_invalid_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not.a.token")
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
