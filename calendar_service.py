"""
Calendar service implementing Backend Proxy Pattern.

This is the core of Option 2: Backend Proxy Pattern.

Flow:
1. ElevenLabs agent calls tool endpoint with user_id
2. This service receives the call
3. Looks up user's OAuth token from database
4. Calls Calendar MCP Server with that token
5. Returns results to ElevenLabs agent

This decouples ElevenLabs from direct calendar access and centralizes
token management in the backend.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
import config
import database
import auth_service
import requests
from colorama import Fore, init

init(autoreset=True)


class CalendarServiceError(Exception):
    """Raised when calendar operations fail"""
    pass


# ============================================================================
# CALENDAR MCP INTEGRATION
# ============================================================================

def call_calendar_mcp(
    user_id: str,
    db: Session,
    operation: str,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Call Calendar MCP Server with user's OAuth token.

    This is the backend proxy - translates calls from ElevenLabs into
    calendar MCP calls authenticated with user's OAuth token.

    Args:
        user_id: User ID to look up OAuth token
        db: Database session
        operation: MCP operation to perform (list_events, create_event, etc.)
        **kwargs: Operation-specific parameters

    Returns:
        dict: Result from calendar MCP
    """
    # Get user and their OAuth token
    oauth_token = auth_service.get_user_oauth_token(db, user_id)
    if not oauth_token:
        raise CalendarServiceError(
            f"User {user_id} has no valid OAuth token"
        )

    # Extract access token
    access_token = oauth_token.get("access_token")
    if not access_token:
        raise CalendarServiceError("No access token in OAuth data")

    try:
        # Prepare MCP call headers with OAuth token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # TODO: Implement actual MCP calls
        # For now, this is the integration point where calendar MCP
        # would be called with the authenticated token

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Calendar MCP call: {operation}")
            print(f"{Fore.CYAN}[DEBUG] User: {user_id}")
            print(f"{Fore.CYAN}[DEBUG] OAuth token present: {bool(access_token)}")

        # Example MCP response structure
        return {
            "success": True,
            "operation": operation,
            "data": kwargs
        }

    except Exception as e:
        error_msg = f"Calendar MCP error: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        raise CalendarServiceError(error_msg)


# ============================================================================
# AVAILABILITY CHECKING (Called by ElevenLabs Agent)
# ============================================================================

def check_availability(
    user_id: str,
    db: Session,
    date: str,
    time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check doctor's calendar availability for a given date.

    Called by ElevenLabs agent tool: check_calendar_availability

    Backend Proxy Pattern:
    1. ElevenLabs agent calls /api/calendar/check-availability with user_id
    2. We look up user's OAuth token
    3. Call Calendar MCP with that token
    4. Return available slots to agent

    Args:
        user_id: Doctor's user ID (from ElevenLabs context)
        db: Database session
        date: Date to check (YYYY-MM-DD or natural language)
        time: Optional specific time to check

    Returns:
        dict: Available slots or error

    Example response to ElevenLabs:
    {
        "success": true,
        "date": "2026-02-15",
        "available_slots": [
            {"time": "14:00", "duration_minutes": 30},
            {"time": "15:00", "duration_minutes": 30}
        ]
    }
    """
    try:
        # TODO: Parse natural language date ("next Tuesday", etc.)
        parsed_date = date  # For now, assume YYYY-MM-DD format

        # Call Calendar MCP to get available slots
        result = call_calendar_mcp(
            user_id=user_id,
            db=db,
            operation="get_available_slots",
            date=parsed_date,
            duration_minutes=config.APPOINTMENT_DURATION_MINUTES,
            buffer_minutes=config.APPOINTMENT_BUFFER_MINUTES
        )

        if not result["success"]:
            return {
                "success": False,
                "error": "Could not check calendar availability"
            }

        # TODO: Mock available slots - replace with real Calendar MCP call
        available_slots = [
            {"time": "14:00", "duration_minutes": 30},
            {"time": "15:00", "duration_minutes": 30},
            {"time": "16:00", "duration_minutes": 30}
        ]

        return {
            "success": True,
            "date": parsed_date,
            "available_slots": available_slots
        }

    except CalendarServiceError as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# APPOINTMENT CREATION (Called by ElevenLabs Agent)
# ============================================================================

def book_appointment(
    user_id: str,
    db: Session,
    patient_name: str,
    patient_phone: str,
    date: str,
    time: str,
    appointment_type: str = "General Checkup"
) -> Dict[str, Any]:
    """
    Book an appointment in calendar and database.

    Called by ElevenLabs agent tool: book_appointment

    Backend Proxy Pattern:
    1. ElevenLabs agent calls /api/appointments with user_id and patient details
    2. We create Calendar event with user's OAuth token via Calendar MCP
    3. Store appointment in database
    4. Send SMS confirmation via Twilio
    5. Return confirmation to agent

    Args:
        user_id: Doctor's user ID
        db: Database session
        patient_name: Patient name
        patient_phone: Patient phone (E.164 format)
        date: Appointment date (YYYY-MM-DD)
        time: Appointment time (HH:MM)
        appointment_type: Type of appointment

    Returns:
        dict: Booking result with confirmation details

    Example response to ElevenLabs:
    {
        "success": true,
        "appointment_id": "appt_abc123",
        "confirmation_number": "CP-20260215-001",
        "message": "Appointment confirmed for John Doe on 2026-02-15 at 14:00"
    }
    """
    try:
        # Get doctor user
        doctor = auth_service.get_user_by_id(db, user_id)
        if not doctor:
            return {
                "success": False,
                "error": "Doctor not found"
            }

        # Find or create patient
        patient = db.query(database.Patient).filter(
            database.Patient.doctor_id == user_id,
            database.Patient.phone == patient_phone
        ).first()

        if not patient:
            patient_id = f"pat_{__import__('uuid').uuid4().hex[:12]}"
            patient = database.Patient(
                id=patient_id,
                doctor_id=user_id,
                name=patient_name,
                phone=patient_phone
            )
            db.add(patient)
            db.flush()

        # Create calendar event via Calendar MCP
        calendar_result = call_calendar_mcp(
            user_id=user_id,
            db=db,
            operation="create_event",
            title=f"Appointment: {patient_name}",
            start_date=date,
            start_time=time,
            duration_minutes=config.APPOINTMENT_DURATION_MINUTES,
            description=f"Patient: {patient_name}\nPhone: {patient_phone}\nType: {appointment_type}\nStatus: scheduled\nReminder Sent: false"
        )

        # TODO: Extract calendar event ID from calendar_result
        calendar_event_id = calendar_result.get("event_id")

        # Create appointment record in database
        appointment_id = f"appt_{__import__('uuid').uuid4().hex[:12]}"
        appointment = database.Appointment(
            id=appointment_id,
            doctor_id=user_id,
            patient_id=patient.id,
            calendar_event_id=calendar_event_id,
            date=date,
            time=time,
            type=appointment_type,
            status="scheduled",
            reminder_sent=False
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # TODO: Send SMS confirmation via Twilio
        # twilio.send_sms(
        #     to_number=patient_phone,
        #     message=f"Hi {patient_name}, your appointment is confirmed for {date} at {time}. Reply STOP to opt out."
        # )

        confirmation_number = f"CP-{date.replace('-', '')}-{appointment_id[:3].upper()}"

        if config.DEBUG:
            print(f"{Fore.GREEN}[DEBUG] Appointment created: {appointment_id}")

        return {
            "success": True,
            "appointment_id": appointment_id,
            "confirmation_number": confirmation_number,
            "message": f"Appointment confirmed for {patient_name} on {date} at {time}. Confirmation number: {confirmation_number}"
        }

    except Exception as e:
        error_msg = f"Failed to book appointment: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# APPOINTMENT CANCELLATION (Called by Patient)
# ============================================================================

def cancel_appointment(
    user_id: str,
    db: Session,
    appointment_id: str
) -> Dict[str, Any]:
    """
    Cancel an appointment.

    Args:
        user_id: Doctor's user ID
        db: Database session
        appointment_id: Appointment to cancel

    Returns:
        dict: Cancellation result
    """
    try:
        appointment = db.query(database.Appointment).filter(
            database.Appointment.id == appointment_id,
            database.Appointment.doctor_id == user_id
        ).first()

        if not appointment:
            return {
                "success": False,
                "error": "Appointment not found"
            }

        # Delete calendar event via Calendar MCP
        if appointment.calendar_event_id:
            call_calendar_mcp(
                user_id=user_id,
                db=db,
                operation="delete_event",
                event_id=appointment.calendar_event_id
            )

        # Update appointment status
        appointment.status = "cancelled"
        appointment.updated_at = datetime.utcnow()
        db.commit()

        # TODO: Send cancellation SMS to patient

        if config.DEBUG:
            print(f"{Fore.GREEN}[DEBUG] Appointment cancelled: {appointment_id}")

        return {
            "success": True,
            "message": "Appointment cancelled"
        }

    except Exception as e:
        error_msg = f"Failed to cancel appointment: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# LIST UPCOMING APPOINTMENTS
# ============================================================================

def get_upcoming_appointments(
    user_id: str,
    db: Session,
    days_ahead: int = 30
) -> List[Dict[str, Any]]:
    """
    Get upcoming appointments for doctor.

    Args:
        user_id: Doctor's user ID
        db: Database session
        days_ahead: Number of days to look ahead

    Returns:
        list: List of upcoming appointments
    """
    try:
        # Query upcoming appointments from database
        future_date = (datetime.utcnow() + timedelta(days=days_ahead)).date()

        appointments = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == user_id,
            database.Appointment.date <= future_date.isoformat(),
            database.Appointment.status.in_(["scheduled", "confirmed"])
        ).order_by(database.Appointment.date, database.Appointment.time).all()

        return [
            {
                "id": appt.id,
                "patient_name": appt.patient.name,
                "patient_phone": appt.patient.phone,
                "date": appt.date,
                "time": appt.time,
                "type": appt.type,
                "status": appt.status
            }
            for appt in appointments
        ]

    except Exception as e:
        error_msg = f"Failed to get appointments: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        return []
