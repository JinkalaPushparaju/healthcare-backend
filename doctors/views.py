from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Doctor
from .serializers import DoctorSerializer


class DoctorListCreateView(ListCreateAPIView):
    """GET /api/doctors/ and POST /api/doctors/ (authenticated users)."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class DoctorDetailView(RetrieveUpdateDestroyAPIView):
    """GET / PUT / DELETE /api/doctors/<id>/ (authenticated users)."""

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
