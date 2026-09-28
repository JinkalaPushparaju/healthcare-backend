"""Root URL configuration."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/doctors/", include("doctors.urls")),
    path("api/mappings/", include("mappings.urls")),
]

# JSON responses for errors raised outside DRF views (unknown URLs, crashes).
handler404 = "core.views.not_found"
handler500 = "core.views.server_error"
