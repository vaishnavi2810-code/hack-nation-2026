"""
Calendar service and appointment management.
"""

from src.calendar.service import (
    CalendarServiceError,
    check_availability,
    book_appointment,
    cancel_appointment,
    get_upcoming_appointments,
)

__all__ = [
    "CalendarServiceError",
    "check_availability",
    "book_appointment",
    "cancel_appointment",
    "get_upcoming_appointments",
]
