"""
Pydantic models for request/response validation.

Defines schemas for:
- Authentication
- Doctors and Patients
- Appointments and Calls
- Calendar operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class SignupRequest(BaseModel):
    """Request to create new doctor account"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1)
    phone: str


class LoginRequest(BaseModel):
    """Request to authenticate doctor"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """Request to logout"""
    pass


# ============================================================================
# DOCTOR MODELS
# ============================================================================

class DoctorProfile(BaseModel):
    """Doctor profile information"""
    id: str
    email: str
    name: str
    phone: str
    timezone: str
    calendar_connected: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CALENDAR MODELS
# ============================================================================

class CalendarAuthUrl(BaseModel):
    """Response containing Google Calendar auth URL"""
    auth_url: str
    state: str


class CalendarCallback(BaseModel):
    """Callback from Google OAuth"""
    code: str
    state: str


class CalendarStatus(BaseModel):
    """Current calendar connection status"""
    connected: bool
    calendar_id: Optional[str] = None
    email: Optional[str] = None
    connected_at: Optional[datetime] = None


class CalendarDisconnect(BaseModel):
    """Request to disconnect calendar"""
    pass


class AvailabilitySlot(BaseModel):
    """Available appointment time slot"""
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    duration_minutes: int


class AvailabilityRequest(BaseModel):
    """Request to check available slots"""
    date: str  # YYYY-MM-DD or natural language like "next Tuesday"


class AvailabilityResponse(BaseModel):
    """Response with available appointment slots"""
    success: bool
    date: str
    available_slots: List[AvailabilitySlot] = []
    error: Optional[str] = None


# ============================================================================
# PATIENT MODELS
# ============================================================================

class PatientCreate(BaseModel):
    """Request to create new patient"""
    name: str = Field(..., min_length=1)
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None


class PatientUpdate(BaseModel):
    """Request to update patient"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    """Patient information response"""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    last_appointment: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# APPOINTMENT MODELS
# ============================================================================

class AppointmentCreate(BaseModel):
    """Request to create new appointment"""
    patient_id: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    type: Optional[str] = "General Checkup"
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Request to update appointment"""
    date: Optional[str] = None
    time: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Appointment information response"""
    id: str
    calendar_event_id: Optional[str] = None
    patient_id: str
    patient_name: str
    date: str
    time: str
    duration_minutes: int
    type: str
    status: str  # scheduled, confirmed, completed, cancelled, no_show
    notes: Optional[str] = None
    reminder_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpcomingAppointmentsResponse(BaseModel):
    """Response with list of upcoming appointments"""
    count: int
    appointments: List[AppointmentResponse]


class AppointmentConfirm(BaseModel):
    """Request to confirm appointment"""
    pass


# ============================================================================
# CALL MODELS
# ============================================================================

class CallCreate(BaseModel):
    """Request to initiate manual outbound call"""
    patient_id: str
    message: str
    call_type: Optional[str] = "manual"  # manual, reminder, confirmation


class CallResponse(BaseModel):
    """Call information response"""
    id: str
    call_sid: str  # Twilio Call SID
    patient_id: str
    patient_name: str
    phone: str
    type: str
    status: str  # initiated, ringing, in-progress, completed, failed
    duration_seconds: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledCallsResponse(BaseModel):
    """Response with list of scheduled calls"""
    count: int
    calls: List[CallResponse]


# ============================================================================
# DASHBOARD MODELS
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_patients: int
    total_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    no_show_count: int
    total_calls_made: int
    successful_calls: int


class DashboardActivity(BaseModel):
    """Recent dashboard activity"""
    recent_appointments: List[AppointmentResponse]
    recent_calls: List[CallResponse]
    upcoming_events: List[AppointmentResponse]


# ============================================================================
# SETTINGS MODELS
# ============================================================================

class SettingsUpdate(BaseModel):
    """Request to update application settings"""
    appointment_duration_minutes: Optional[int] = None
    reminder_hours_before: Optional[int] = None
    timezone: Optional[str] = None
    enable_sms_confirmations: Optional[bool] = None
    enable_reminders: Optional[bool] = None


class SettingsResponse(BaseModel):
    """Application settings response"""
    appointment_duration_minutes: int
    reminder_hours_before: int
    timezone: str
    enable_sms_confirmations: bool
    enable_reminders: bool
    enable_outbound_calls: bool


# ============================================================================
# WEBHOOK MODELS
# ============================================================================

class ElevenLabsWebhookPayload(BaseModel):
    """Payload from ElevenLabs webhook"""
    call_id: str
    agent_id: str
    from_number: str
    to_number: str
    call_type: str  # inbound, outbound
    duration_seconds: Optional[int] = None
    status: Optional[str] = None
    transcript: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional fields from ElevenLabs


class CallbackPayload(BaseModel):
    """Generic callback payload for various webhooks"""
    event_type: str
    data: dict

    class Config:
        extra = "allow"


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[dict]
