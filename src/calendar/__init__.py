"""
CallPilot Calendar Module

Provides Google Calendar integration for appointment management.
"""

from src.calendar.availability import (
    check_availability,
    is_slot_available,
    parse_date
)
from src.calendar.appointments import (
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    get_appointment,
    get_appointments_by_phone,
    get_upcoming_appointments,
    mark_reminder_sent,
    mark_no_show
)
from src.calendar.models import (
    Appointment,
    Patient,
    TimeSlot,
    AppointmentStatus,
    AppointmentType,
    AvailabilityResponse,
    BookingResponse
)

__all__ = [
    # Availability
    "check_availability",
    "is_slot_available",
    "parse_date",
    # Appointments
    "book_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    "get_appointment",
    "get_appointments_by_phone",
    "get_upcoming_appointments",
    "mark_reminder_sent",
    "mark_no_show",
    # Models
    "Appointment",
    "Patient",
    "TimeSlot",
    "AppointmentStatus",
    "AppointmentType",
    "AvailabilityResponse",
    "BookingResponse"
]