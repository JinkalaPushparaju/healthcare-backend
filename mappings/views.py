from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.models import Doctor
from patients.models import Patient

from .models import PatientDoctorMapping
from .serializers import (
    AssignedDoctorSerializer,
    MappingCreateSerializer,
    MappingDetailSerializer,
    MappingSummarySerializer,
)


def user_mappings(user):
    """Mappings whose patient belongs to the given user."""
    return PatientDoctorMapping.objects.filter(patient__created_by=user)


class MappingListCreateView(APIView):
    """GET /api/mappings/ and POST /api/mappings/"""

    def get(self, request):
        queryset = user_mappings(request.user).select_related("patient", "doctor")
        return Response(MappingDetailSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = MappingCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            mapping = serializer.save()
        except IntegrityError:  # concurrent duplicate request
            return Response(
                {"error": "This doctor is already assigned to this patient."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Doctor assigned to patient successfully",
                "mapping": MappingSummarySerializer(mapping).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MappingDetailView(APIView):
    """
    GET    /api/mappings/<patient_id>/ - doctors assigned to a patient
    DELETE /api/mappings/<id>/         - remove a patient-doctor mapping
    """

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk, created_by=request.user)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found")
        doctors = Doctor.objects.filter(patient_mappings__patient=patient).order_by(
            "id"
        )
        return Response(AssignedDoctorSerializer(doctors, many=True).data)

    def delete(self, request, pk):
        try:
            mapping = user_mappings(request.user).get(pk=pk)
        except PatientDoctorMapping.DoesNotExist:
            raise NotFound("Mapping not found")
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
