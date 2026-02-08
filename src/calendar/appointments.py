"""
Functions to manage appointments in Google Calendar.
Book, cancel, reschedule, and query appointments.
"""

from datetime import datetime, timedelta
from typing import List, Optional
import pytz

from src.config import calendar_config
from src.calendar.client import get_calendar_service
from src.calendar.models import (
    Appointment, Patient, AppointmentStatus, AppointmentType,
    BookingRequest, BookingResponse, TimeSlot
)
from src.calendar.availability import is_slot_available


def book_appointment(
    patient_name: str,
    patient_phone: str,
    appointment_datetime: datetime,
    patient_email: Optional[str] = None,
    appointment_type: AppointmentType = AppointmentType.CHECKUP,
    notes: Optional[str] = None
) -> BookingResponse:
    """
    Book a new appointment by creating a Google Calendar event.
    
    Args:
        patient_name: Full name of the patient
        patient_phone: Phone number for SMS confirmation
        appointment_datetime: When the appointment starts
        patient_email: Optional email address
        appointment_type: Type of appointment
        notes: Additional notes
    
    Returns:
        BookingResponse with success status and appointment details
    """
    service = get_calendar_service()
    tz = pytz.timezone(calendar_config.timezone)
    
    # Ensure datetime is timezone-aware
    if appointment_datetime.tzinfo is None:
        appointment_datetime = tz.localize(appointment_datetime)
    
    # Check if slot is available
    if not is_slot_available(appointment_datetime):
        return BookingResponse(
            success=False,
            message=f"The time slot at {appointment_datetime.strftime('%-I:%M %p')} is not available. "
                    "Please check availability and try another time."
        )
    
    # Create patient and appointment objects
    patient = Patient(
        name=patient_name,
        phone=patient_phone,
        email=patient_email,
        notes=notes
    )
    
    end_time = appointment_datetime + timedelta(
        minutes=calendar_config.appointment_duration_minutes
    )
    
    appointment = Appointment(
        patient=patient,
        start_time=appointment_datetime,
        end_time=end_time,
        appointment_type=appointment_type,
        status=AppointmentStatus.SCHEDULED,
        reminder_sent=False
    )
    
    # Create Google Calendar event
    event = {
        "summary": f"Appointment: {patient_name}",
        "description": appointment.to_calendar_description(),
        "start": {
            "dateTime": appointment_datetime.isoformat(),
            "timeZone": calendar_config.timezone
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": calendar_config.timezone
        },
        "reminders": {
            "useDefault": False,
            "overrides": []
        }
    }
    
    try:
        created_event = service.events().insert(
            calendarId=calendar_config.calendar_id,
            body=event
        ).execute()
        
        appointment.id = created_event["id"]
        
        return BookingResponse(
            success=True,
            appointment=appointment,
            message=f"Appointment booked for {appointment.formatted_date} at {appointment.formatted_time}. "
                    f"You'll receive a reminder call 3 hours before your appointment.",
            confirmation_id=created_event["id"]
        )
    except Exception as e:
        return BookingResponse(
            success=False,
            message=f"Failed to book appointment: {str(e)}"
        )


def cancel_appointment(appointment_id: str) -> BookingResponse:
    """
    Cancel an appointment by deleting or updating the Google Calendar event.
    
    Args:
        appointment_id: Google Calendar event ID
    
    Returns:
        BookingResponse with success status
    """
    service = get_calendar_service()
    
    try:
        # Get the existing event first
        event = service.events().get(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id
        ).execute()
        
        # Update status in description instead of deleting
        description = event.get("description", "")
        description = description.replace(
            "Status: scheduled", 
            "Status: cancelled"
        ).replace(
            "Status: confirmed",
            "Status: cancelled"
        )
        
        event["description"] = description
        event["summary"] = event["summary"].replace("Appointment:", "CANCELLED:")
        
        service.events().update(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id,
            body=event
        ).execute()
        
        return BookingResponse(
            success=True,
            message="Appointment has been cancelled."
        )
    except Exception as e:
        return BookingResponse(
            success=False,
            message=f"Failed to cancel appointment: {str(e)}"
        )


def reschedule_appointment(
    appointment_id: str,
    new_datetime: datetime
) -> BookingResponse:
    """
    Reschedule an existing appointment to a new time.
    
    Args:
        appointment_id: Google Calendar event ID
        new_datetime: New appointment time
    
    Returns:
        BookingResponse with updated appointment details
    """
    service = get_calendar_service()
    tz = pytz.timezone(calendar_config.timezone)
    
    # Ensure datetime is timezone-aware
    if new_datetime.tzinfo is None:
        new_datetime = tz.localize(new_datetime)
    
    # Check if new slot is available
    if not is_slot_available(new_datetime):
        return BookingResponse(
            success=False,
            message=f"The new time slot at {new_datetime.strftime('%-I:%M %p')} is not available."
        )
    
    try:
        # Get existing event
        event = service.events().get(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id
        ).execute()
        
        # Calculate new end time
        new_end = new_datetime + timedelta(
            minutes=calendar_config.appointment_duration_minutes
        )
        
        # Update event times
        event["start"] = {
            "dateTime": new_datetime.isoformat(),
            "timeZone": calendar_config.timezone
        }
        event["end"] = {
            "dateTime": new_end.isoformat(),
            "timeZone": calendar_config.timezone
        }
        
        # Reset reminder status
        description = event.get("description", "")
        description = description.replace("Reminder Sent: true", "Reminder Sent: false")
        event["description"] = description
        
        updated_event = service.events().update(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id,
            body=event
        ).execute()
        
        appointment = Appointment.from_calendar_event(updated_event)
        
        return BookingResponse(
            success=True,
            appointment=appointment,
            message=f"Appointment rescheduled to {appointment.formatted_date} at {appointment.formatted_time}.",
            confirmation_id=appointment_id
        )
    except Exception as e:
        return BookingResponse(
            success=False,
            message=f"Failed to reschedule appointment: {str(e)}"
        )


def get_appointment(appointment_id: str) -> Optional[Appointment]:
    """
    Get a specific appointment by ID.
    """
    service = get_calendar_service()
    
    try:
        event = service.events().get(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id
        ).execute()
        return Appointment.from_calendar_event(event)
    except Exception:
        return None


def get_appointments_by_phone(phone: str) -> List[Appointment]:
    """
    Find all appointments for a patient by phone number.
    """
    service = get_calendar_service()
    tz = pytz.timezone(calendar_config.timezone)
    now = datetime.now(tz)
    
    # Search upcoming events
    events_result = service.events().list(
        calendarId=calendar_config.calendar_id,
        timeMin=now.isoformat(),
        maxResults=50,
        singleEvents=True,
        orderBy="startTime",
        q=phone  # Search by phone number in description
    ).execute()
    
    events = events_result.get("items", [])
    appointments = []
    
    for event in events:
        if event.get("summary", "").startswith("Appointment:"):
            appointment = Appointment.from_calendar_event(event)
            if appointment.patient.phone == phone:
                appointments.append(appointment)
    
    return appointments


def get_upcoming_appointments(hours_ahead: int = 3) -> List[Appointment]:
    """
    Get appointments happening within the next N hours.
    Used for the reminder cron job.
    
    Args:
        hours_ahead: How many hours ahead to look
    
    Returns:
        List of appointments that need reminders
    """
    service = get_calendar_service()
    tz = pytz.timezone(calendar_config.timezone)
    now = datetime.now(tz)
    
    # Time window for reminders
    window_start = now + timedelta(hours=hours_ahead - 0.5)
    window_end = now + timedelta(hours=hours_ahead + 0.5)
    
    events_result = service.events().list(
        calendarId=calendar_config.calendar_id,
        timeMin=window_start.isoformat(),
        timeMax=window_end.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    appointments = []
    
    for event in events:
        if event.get("summary", "").startswith("Appointment:"):
            appointment = Appointment.from_calendar_event(event)
            # Only include appointments that haven't received reminders
            if not appointment.reminder_sent and appointment.status == AppointmentStatus.SCHEDULED:
                appointments.append(appointment)
    
    return appointments


def mark_reminder_sent(appointment_id: str) -> bool:
    """
    Update appointment to mark reminder as sent.
    """
    service = get_calendar_service()
    
    try:
        event = service.events().get(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id
        ).execute()
        
        description = event.get("description", "")
        description = description.replace("Reminder Sent: false", "Reminder Sent: true")
        event["description"] = description
        
        service.events().update(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id,
            body=event
        ).execute()
        
        return True
    except Exception:
        return False


def mark_no_show(appointment_id: str) -> BookingResponse:
    """
    Mark an appointment as a no-show.
    This triggers follow-up workflow.
    """
    service = get_calendar_service()
    
    try:
        event = service.events().get(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id
        ).execute()
        
        description = event.get("description", "")
        description = description.replace("Status: scheduled", "Status: no_show")
        description = description.replace("Status: confirmed", "Status: no_show")
        event["description"] = description
        event["summary"] = event["summary"].replace("Appointment:", "NO SHOW:")
        
        service.events().update(
            calendarId=calendar_config.calendar_id,
            eventId=appointment_id,
            body=event
        ).execute()
        
        return BookingResponse(
            success=True,
            message="Appointment marked as no-show. Follow-up will be scheduled."
        )
    except Exception as e:
        return BookingResponse(
            success=False,
            message=f"Failed to update appointment: {str(e)}"
        )