from rest_framework import status

from core.tests import AuthenticatedAPITestCase
from doctors.models import Doctor

LIST_URL = "/api/doctors/"
PAYLOAD = {
    "name": "Dr. Smith",
    "specialization": "Cardiologist",
    "phone": "9876543210",
    "email": "doctor@example.com",
    "address": "Hyderabad",
}


class DoctorTests(AuthenticatedAPITestCase):
    def create_doctor(self, **overrides):
        return Doctor.objects.create(**{**PAYLOAD, **overrides})

    def test_create_doctor(self):
        response = self.client.post(LIST_URL, PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Dr. Smith")

    def test_create_doctor_validation(self):
        self.create_doctor()
        for bad in ({"email": "doctor@example.com"}, {"email": "x"}, {"phone": "abc"}):
            response = self.client.post(LIST_URL, {**PAYLOAD, **bad}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad)

    def test_list_doctors(self):
        self.create_doctor()
        self.create_doctor(name="Dr. Kumar", email="kumar@example.com")
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_doctor(self):
        doctor = self.create_doctor()
        response = self.client.get(f"{LIST_URL}{doctor.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["specialization"], "Cardiologist")

    def test_get_missing_doctor(self):
        response = self.client.get(f"{LIST_URL}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_doctor(self):
        doctor = self.create_doctor()
        response = self.client.put(
            f"{LIST_URL}{doctor.id}/",
            {**PAYLOAD, "specialization": "Neurologist"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doctor.refresh_from_db()
        self.assertEqual(doctor.specialization, "Neurologist")

    def test_delete_doctor(self):
        doctor = self.create_doctor()
        response = self.client.delete(f"{LIST_URL}{doctor.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(pk=doctor.id).exists())

    def test_unauthenticated_access(self):
        self.client.credentials()
        self.assertEqual(
            self.client.get(LIST_URL).status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(
            self.client.post(LIST_URL, PAYLOAD, format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
