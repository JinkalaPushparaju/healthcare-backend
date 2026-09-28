"""Consistent JSON error responses for the whole API.

* Validation errors keep DRF's field-keyed format:
  ``{"email": ["A user with this email already exists."]}``
* Every other error is returned as ``{"error": "<message>"}``.
* Unexpected exceptions return a generic 500 without leaking internals.
"""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": str(response.data["detail"])}

    return response
