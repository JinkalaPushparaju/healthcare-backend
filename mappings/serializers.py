from rest_framework import serializers
from rest_framework.exceptions import NotFound

from doctors.models import Doctor
from patients.models import Patient

from .models import PatientDoctorMapping


class MappingCreateSerializer(serializers.Serializer):
    """Validates the request body of POST /api/mappings/."""

    patient = serializers.IntegerField()
    doctor = serializers.IntegerField()

    def validate_patient(self, value):
        user = self.context["request"].user
        # Patients of other users are treated as non-existent.
        try:
            return Patient.objects.get(pk=value, created_by=user)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found")

    def validate_doctor(self, value):
        try:
            return Doctor.objects.get(pk=value)
        except Doctor.DoesNotExist:
            raise NotFound("Doctor not found")

    def validate(self, attrs):
        if PatientDoctorMapping.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                {"error": "This doctor is already assigned to this patient."}
            )
        return attrs

    def create(self, validated_data):
        return PatientDoctorMapping.objects.create(**validated_data)


class MappingSummarySerializer(serializers.ModelSerializer):
    """Compact representation returned right after assignment."""

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient", "doctor")


class _PatientBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ("id", "name")


class _DoctorBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ("id", "name", "specialization")


class MappingDetailSerializer(serializers.ModelSerializer):
    patient = _PatientBriefSerializer(read_only=True)
    doctor = _DoctorBriefSerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient", "doctor", "assigned_at")


class AssignedDoctorSerializer(serializers.ModelSerializer):
    """Doctor as listed under a patient."""

    class Meta:
        model = Doctor
        fields = ("id", "name", "specialization")
