from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Patient
from .serializers import PatientSerializer


class OwnedPatientQuerysetMixin:
    """Restrict patients to those created by the requesting user.

    Records owned by someone else behave as if they do not exist (404),
    so their existence is never revealed.
    """

    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)


class PatientListCreateView(OwnedPatientQuerysetMixin, ListCreateAPIView):
    """GET /api/patients/ and POST /api/patients/"""

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PatientDetailView(OwnedPatientQuerysetMixin, RetrieveUpdateDestroyAPIView):
    """GET / PUT / DELETE /api/patients/<id>/"""
