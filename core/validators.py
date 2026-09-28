"""Reusable field validators."""
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Enter a valid phone number (7-15 digits, optional leading +).",
)
