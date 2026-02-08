"""
Pydantic schemas for Calendar API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# ============== Enums ==============

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class AppointmentType(str, Enum):
    CHECKUP = "checkup"
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    URGENT = "urgent"
    OTHER = "other"


# ============== Common Models ==============

class TimeSlot(BaseModel):
    """A single available time slot."""
    start: datetime
    end: datetime
    formatted_time: str = Field(..., description="Human readable time, e.g., '2:00 PM'")
    formatted_date: str = Field(..., description="Human readable date, e.g., 'Tuesday, February 11'")


class Patient(BaseModel):
    """Patient information."""
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None


class Appointment(BaseModel):
    """Full appointment details."""
    id: str
    patient: Patient
    start_time: datetime
    end_time: datetime
    formatted_time: str
    formatted_date: str
    appointment_type: AppointmentType
    status: AppointmentStatus
    reminder_sent: bool = False


# ============== Request Schemas ==============

class CheckAvailabilityRequest(BaseModel):
    """Request to check availability for a single date."""
    date: str = Field(..., description="Date to check: 'tomorrow', 'next tuesday', '2026-02-15'")
    duration_minutes: Optional[int] = Field(None, description="Override default duration")


class CheckAvailabilityRangeRequest(BaseModel):
    """Request to check availability across multiple dates."""
    dates: List[str] = Field(..., description="List of dates to check")
    duration_minutes: Optional[int] = Field(None, description="Override default duration")


class CreateAppointmentRequest(BaseModel):
    """Request to book a new appointment."""
    patient_name: str = Field(..., description="Patient full name")
    patient_phone: str = Field(..., description="Patient phone number")
    patient_email: Optional[str] = Field(None, description="Patient email")
    appointment_datetime: datetime = Field(..., description="Appointment start time")
    appointment_type: AppointmentType = Field(default=AppointmentType.CHECKUP)
    notes: Optional[str] = Field(None, description="Additional notes")


class RescheduleAppointmentRequest(BaseModel):
    """Request to reschedule an appointment."""
    new_datetime: datetime = Field(..., description="New appointment time")


class AuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    code: str = Field(..., description="Authorization code from Google")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


# ============== Response Schemas ==============

class CalendarStatusResponse(BaseModel):
    """Response for calendar connection status."""
    connected: bool
    email: Optional[str] = None
    calendar_id: Optional[str] = None
    message: str


class AvailabilityResponse(BaseModel):
    """Response with available slots for a single date."""
    date: str
    formatted_date: str
    available_slots: List[TimeSlot]
    total_slots: int
    message: str


class AvailabilityRangeResponse(BaseModel):
    """Response with available slots across multiple dates."""
    dates: List[AvailabilityResponse]
    total_slots: int
    message: str


class AppointmentResponse(BaseModel):
    """Response for single appointment operations."""
    success: bool
    message: str
    appointment: Optional[Appointment] = None


class AppointmentCreateResponse(BaseModel):
    """Response after creating an appointment."""
    success: bool
    message: str
    confirmation_id: Optional[str] = None
    appointment: Optional[Appointment] = None


class AppointmentCancelResponse(BaseModel):
    """Response after cancelling an appointment."""
    success: bool
    message: str
    appointment_id: str


class UpcomingAppointmentsResponse(BaseModel):
    """Response with list of upcoming appointments."""
    appointments: List[Appointment]
    total: int
    message: str


class AppointmentRemindResponse(BaseModel):
    """Response after marking reminder sent."""
    success: bool
    message: str
    appointment_id: str
    reminder_sent: bool


class AppointmentNoShowResponse(BaseModel):
    """Response after marking no-show."""
    success: bool
    message: str
    appointment_id: str
    status: AppointmentStatus


class CalendarEventsResponse(BaseModel):
    """Response with raw calendar events."""
    events: List[dict]
    total: int
    message: str


class CalendarAuthUrlResponse(BaseModel):
    """Response with OAuth URL."""
    auth_url: str
    message: str


class CalendarAuthResponse(BaseModel):
    """Response after OAuth callback."""
    success: bool
    message: str
    email: Optional[str] = None


class DisconnectResponse(BaseModel):
    """Response after disconnecting calendar."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None