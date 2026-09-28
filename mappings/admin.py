from django.contrib import admin

from .models import PatientDoctorMapping


@admin.register(PatientDoctorMapping)
class PatientDoctorMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "assigned_at")
    list_filter = ("assigned_at", "doctor__specialization")
    search_fields = ("patient__name", "doctor__name", "doctor__specialization")
    autocomplete_fields = ("patient", "doctor")
