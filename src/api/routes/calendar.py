"""
Calendar API Routes

All /api/calendar/* endpoints.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from src.core.auth import auth_manager
from src.services.calendar_service import calendar_service
from src.api.schemas.calendar import (
    # Requests
    CheckAvailabilityRequest,
    CheckAvailabilityRangeRequest,
    CreateAppointmentRequest,
    RescheduleAppointmentRequest,
    AuthCallbackRequest,
    # Responses
    CalendarStatusResponse,
    AvailabilityResponse,
    AvailabilityRangeResponse,
    AppointmentResponse,
    AppointmentCreateResponse,
    AppointmentCancelResponse,
    UpcomingAppointmentsResponse,
    AppointmentRemindResponse,
    AppointmentNoShowResponse,
    CalendarEventsResponse,
    CalendarAuthUrlResponse,
    CalendarAuthResponse,
    DisconnectResponse,
    # Models
    TimeSlot,
    AppointmentStatus
)

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


# ============== Auth Endpoints ==============

@router.get("/status", response_model=CalendarStatusResponse)
def get_calendar_status():
    """Check if Google Calendar is connected."""
    connected, email, calendar_id = auth_manager.get_status()
    
    return CalendarStatusResponse(
        connected=connected,
        email=email,
        calendar_id=calendar_id,
        message="Connected to Google Calendar" if connected else "Not connected"
    )


@router.get("/auth-url", response_model=CalendarAuthUrlResponse)
def get_auth_url():
    """Get Google OAuth authorization URL."""
    auth_url = auth_manager.get_auth_url()
    
    return CalendarAuthUrlResponse(
        auth_url=auth_url,
        message="Redirect user to this URL to authorize"
    )


@router.post("/auth-callback", response_model=CalendarAuthResponse)
def handle_auth_callback(request: AuthCallbackRequest):
    """Handle OAuth callback and exchange code for tokens."""
    success, message, email = auth_manager.handle_callback(request.code)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CalendarAuthResponse(
        success=True,
        message=message,
        email=email
    )


@router.get("/auth-callback", response_model=CalendarAuthResponse)
def handle_auth_callback_get(code: str = Query(...), state: Optional[str] = Query(None)):
    """Handle OAuth callback via GET (redirect from Google)."""
    success, message, email = auth_manager.handle_callback(code)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CalendarAuthResponse(
        success=True,
        message=message,
        email=email
    )


@router.delete("/disconnect", response_model=DisconnectResponse)
def disconnect_calendar():
    """Disconnect Google Calendar by removing stored tokens."""
    success, message = auth_manager.disconnect()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return DisconnectResponse(
        success=True,
        message=message
    )


# ============== Availability Endpoints ==============

@router.post("/check-availability", response_model=AvailabilityResponse)
def check_availability(request: CheckAvailabilityRequest):
    """
    Check available appointment slots for a single date.
    
    Date formats supported:
    - Natural language: "today", "tomorrow", "next tuesday"
    - Standard: "2026-02-15", "02/15/2026"
    """
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    date_str, formatted_date, slots, message = calendar_service.check_availability(
        request.date,
        request.duration_minutes
    )
    
    return AvailabilityResponse(
        date=date_str,
        formatted_date=formatted_date,
        available_slots=slots,
        total_slots=len(slots),
        message=message
    )


@router.post("/check-availability-range", response_model=AvailabilityRangeResponse)
def check_availability_range(request: CheckAvailabilityRangeRequest):
    """
    Check available slots across multiple dates.
    
    Example: ["tuesday", "wednesday"] or ["2026-02-11", "2026-02-12"]
    """
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    results = calendar_service.check_availability_range(
        request.dates,
        request.duration_minutes
    )
    
    date_responses = []
    total_slots = 0
    
    for date_str, formatted_date, slots, message in results:
        date_responses.append(AvailabilityResponse(
            date=date_str,
            formatted_date=formatted_date,
            available_slots=slots,
            total_slots=len(slots),
            message=message
        ))
        total_slots += len(slots)
    
    return AvailabilityRangeResponse(
        dates=date_responses,
        total_slots=total_slots,
        message=f"Found {total_slots} total slots across {len(request.dates)} dates"
    )


# ============== Appointment CRUD ==============

@router.post("/appointments", response_model=AppointmentCreateResponse)
def create_appointment(request: CreateAppointmentRequest):
    """Book a new appointment."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    success, message, confirmation_id, appointment = calendar_service.create_appointment(
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        appointment_datetime=request.appointment_datetime,
        patient_email=request.patient_email,
        appointment_type=request.appointment_type,
        notes=request.notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AppointmentCreateResponse(
        success=True,
        message=message,
        confirmation_id=confirmation_id,
        appointment=appointment
    )


@router.get("/appointments", response_model=UpcomingAppointmentsResponse)
def get_upcoming_appointments(hours_ahead: Optional[int] = Query(None)):
    """
    Get upcoming appointments.
    
    Optional: pass hours_ahead to limit to appointments within N hours.
    """
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    appointments = calendar_service.get_upcoming_appointments(hours_ahead)
    
    return UpcomingAppointmentsResponse(
        appointments=appointments,
        total=len(appointments),
        message=f"Found {len(appointments)} upcoming appointments"
    )


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str):
    """Get a specific appointment by ID."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    appointment = calendar_service.get_appointment(appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return AppointmentResponse(
        success=True,
        message="Appointment found",
        appointment=appointment
    )


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
def reschedule_appointment(appointment_id: str, request: RescheduleAppointmentRequest):
    """Reschedule an existing appointment."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    success, message, appointment = calendar_service.reschedule_appointment(
        appointment_id,
        request.new_datetime
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AppointmentResponse(
        success=True,
        message=message,
        appointment=appointment
    )


@router.delete("/appointments/{appointment_id}", response_model=AppointmentCancelResponse)
def cancel_appointment(appointment_id: str):
    """Cancel an appointment."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    success, message = calendar_service.cancel_appointment(appointment_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AppointmentCancelResponse(
        success=True,
        message=message,
        appointment_id=appointment_id
    )


# ============== Reminder & No-Show ==============

@router.patch("/appointments/{appointment_id}/remind", response_model=AppointmentRemindResponse)
def mark_reminder_sent(appointment_id: str):
    """Mark that a reminder call was sent for this appointment."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    success, message = calendar_service.mark_reminder_sent(appointment_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AppointmentRemindResponse(
        success=True,
        message=message,
        appointment_id=appointment_id,
        reminder_sent=True
    )


@router.patch("/appointments/{appointment_id}/no-show", response_model=AppointmentNoShowResponse)
def mark_no_show(appointment_id: str):
    """Mark an appointment as no-show."""
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    success, message = calendar_service.mark_no_show(appointment_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AppointmentNoShowResponse(
        success=True,
        message=message,
        appointment_id=appointment_id,
        status=AppointmentStatus.NO_SHOW
    )


# ============== Raw Events (Doctor Dashboard) ==============

@router.get("/events", response_model=CalendarEventsResponse)
def get_calendar_events(
    time_min: Optional[datetime] = Query(None),
    time_max: Optional[datetime] = Query(None)
):
    """
    Get raw calendar events (for doctor dashboard).
    
    Optional filters: time_min, time_max
    """
    if not auth_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not connected to Google Calendar")
    
    events = calendar_service.get_all_events(time_min, time_max)
    
    return CalendarEventsResponse(
        events=events,
        total=len(events),
        message=f"Found {len(events)} events"
    )