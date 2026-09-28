from rest_framework import status

from core.tests import AuthenticatedAPITestCase
from patients.models import Patient

LIST_URL = "/api/patients/"
PAYLOAD = {
    "name": "John Doe",
    "age": 35,
    "gender": "Male",
    "phone": "9876543210",
    "address": "Hyderabad",
    "medical_history": "Diabetes",
}


class PatientTests(AuthenticatedAPITestCase):
    def create_patient(self, user=None, **overrides):
        return Patient.objects.create(
            **{**PAYLOAD, **overrides}, created_by=user or self.user
        )

    def test_create_patient(self):
        response = self.client.post(LIST_URL, PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_created_by_cannot_be_spoofed(self):
        response = self.client.post(
            LIST_URL, {**PAYLOAD, "created_by": self.other_user.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_create_patient_validation(self):
        for bad in ({"age": -1}, {"age": 200}, {"phone": "abc"}, {"gender": "X"}):
            response = self.client.post(LIST_URL, {**PAYLOAD, **bad}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_own_patients(self):
        own = self.create_patient()
        self.create_patient(user=self.other_user, name="Other")
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([p["id"] for p in response.data], [own.id])

    def test_get_patient(self):
        patient = self.create_patient()
        response = self.client.get(f"{LIST_URL}{patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "John Doe")

    def test_get_other_users_patient_is_hidden(self):
        patient = self.create_patient(user=self.other_user)
        response = self.client.get(f"{LIST_URL}{patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_missing_patient(self):
        response = self.client.get(f"{LIST_URL}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_update_patient(self):
        patient = self.create_patient()
        response = self.client.put(
            f"{LIST_URL}{patient.id}/",
            {**PAYLOAD, "name": "Updated", "created_by": self.other_user.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patient.refresh_from_db()
        self.assertEqual(patient.name, "Updated")
        self.assertEqual(patient.created_by, self.user)

    def test_update_other_users_patient(self):
        patient = self.create_patient(user=self.other_user)
        response = self.client.put(f"{LIST_URL}{patient.id}/", PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_patient(self):
        patient = self.create_patient()
        response = self.client.delete(f"{LIST_URL}{patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(pk=patient.id).exists())

    def test_delete_other_users_patient(self):
        patient = self.create_patient(user=self.other_user)
        response = self.client.delete(f"{LIST_URL}{patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Patient.objects.filter(pk=patient.id).exists())

    def test_unauthenticated_access(self):
        self.client.credentials()
        for method, url in (
            ("get", LIST_URL),
            ("post", LIST_URL),
            ("get", f"{LIST_URL}1/"),
            ("put", f"{LIST_URL}1/"),
            ("delete", f"{LIST_URL}1/"),
        ):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, url)
