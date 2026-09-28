"""JSON handlers for errors raised outside DRF views."""
from django.http import JsonResponse


def not_found(request, exception=None):
    return JsonResponse({"error": "Resource not found"}, status=404)


def server_error(request):
    return JsonResponse({"error": "Internal server error"}, status=500)
