from rest_framework import status

from core.tests import AuthenticatedAPITestCase
from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from patients.models import Patient

URL = "/api/mappings/"


class MappingTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.patient = Patient.objects.create(
            name="John Doe", age=35, gender="Male", phone="9876543210",
            created_by=self.user,
        )
        self.other_patient = Patient.objects.create(
            name="Other", age=40, gender="Female", phone="9876543211",
            created_by=self.other_user,
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Smith", specialization="Cardiologist",
            phone="9876543210", email="smith@example.com",
        )
        self.doctor2 = Doctor.objects.create(
            name="Dr. Kumar", specialization="Neurologist",
            phone="9876543212", email="kumar@example.com",
        )

    def assign(self, patient=None, doctor=None):
        return PatientDoctorMapping.objects.create(
            patient=patient or self.patient, doctor=doctor or self.doctor
        )

    def test_assign_doctor(self):
        response = self.client.post(
            URL, {"patient": self.patient.id, "doctor": self.doctor.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["message"], "Doctor assigned to patient successfully"
        )
        self.assertEqual(response.data["mapping"]["patient"], self.patient.id)
        self.assertEqual(response.data["mapping"]["doctor"], self.doctor.id)

    def test_duplicate_assignment(self):
        self.assign()
        response = self.client.post(
            URL, {"patient": self.patient.id, "doctor": self.doctor.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_assign_invalid_ids(self):
        response = self.client.post(
            URL, {"patient": 9999, "doctor": self.doctor.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Patient not found"})
        response = self.client.post(
            URL, {"patient": self.patient.id, "doctor": 9999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Doctor not found"})

    def test_assign_missing_fields(self):
        response = self.client.post(URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_assign_other_users_patient(self):
        response = self.client.post(
            URL,
            {"patient": self.other_patient.id, "doctor": self.doctor.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(PatientDoctorMapping.objects.exists())

    def test_list_mappings_only_own(self):
        own = self.assign()
        self.assign(patient=self.other_patient)
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["id"], own.id)
        self.assertEqual(item["patient"], {"id": self.patient.id, "name": "John Doe"})
        self.assertEqual(
            item["doctor"],
            {"id": self.doctor.id, "name": "Dr. Smith", "specialization": "Cardiologist"},
        )
        self.assertIn("assigned_at", item)

    def test_get_doctors_for_patient(self):
        self.assign()
        self.assign(doctor=self.doctor2)
        response = self.client.get(f"{URL}{self.patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [d["id"] for d in response.data], [self.doctor.id, self.doctor2.id]
        )
        self.assertEqual(
            set(response.data[0]), {"id", "name", "specialization"}
        )

    def test_get_doctors_for_other_users_patient(self):
        response = self.client.get(f"{URL}{self.other_patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping(self):
        mapping = self.assign()
        response = self.client.delete(f"{URL}{mapping.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.exists())

    def test_delete_other_users_mapping(self):
        mapping = self.assign(patient=self.other_patient)
        response = self.client.delete(f"{URL}{mapping.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(PatientDoctorMapping.objects.filter(pk=mapping.id).exists())

    def test_delete_missing_mapping(self):
        response = self.client.delete(f"{URL}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access(self):
        self.client.credentials()
        for method, url in (
            ("get", URL),
            ("post", URL),
            ("get", f"{URL}1/"),
            ("delete", f"{URL}1/"),
        ):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, url)
