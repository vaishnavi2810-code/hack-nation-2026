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
from src import config
from src.database import models as database
from src.auth import service as auth_service
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
    print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
    print(f"{Fore.CYAN}[MCP PROXY] call_calendar_mcp() called")
    print(f"{Fore.CYAN}[MCP PROXY] Operation: {operation}")
    print(f"{Fore.CYAN}[MCP PROXY] User ID: {user_id}")
    print(f"{Fore.CYAN}[MCP PROXY] Parameters: {kwargs}")

    try:
        # Get user and their OAuth token
        print(f"{Fore.CYAN}[MCP PROXY] Looking up OAuth token for user {user_id}...")
        oauth_token = auth_service.get_user_oauth_token(db, user_id)
        if not oauth_token:
            error_msg = f"User {user_id} has no valid OAuth token"
            print(f"{Fore.RED}[MCP PROXY] ❌ {error_msg}")
            print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
            raise CalendarServiceError(error_msg)
        print(f"{Fore.GREEN}[MCP PROXY] ✅ OAuth token found")

        # Extract access token
        print(f"{Fore.CYAN}[MCP PROXY] Extracting access token from OAuth data...")
        access_token = oauth_token.get("access_token")
        if not access_token:
            error_msg = "No access token in OAuth data"
            print(f"{Fore.RED}[MCP PROXY] ❌ {error_msg}")
            print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
            raise CalendarServiceError(error_msg)
        print(f"{Fore.GREEN}[MCP PROXY] ✅ Access token extracted (length: {len(access_token)} chars)")

        # Prepare MCP call headers with OAuth token
        print(f"{Fore.CYAN}[MCP PROXY] Preparing MCP call headers with OAuth token...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        print(f"{Fore.GREEN}[MCP PROXY] ✅ Headers prepared")

        # TODO: Implement actual MCP calls
        # For now, this is the integration point where calendar MCP
        # would be called with the authenticated token

        print(f"{Fore.CYAN}[MCP PROXY] Returning mock MCP response for operation: {operation}")

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Calendar MCP call: {operation}")
            print(f"{Fore.CYAN}[DEBUG] User: {user_id}")
            print(f"{Fore.CYAN}[DEBUG] OAuth token present: {bool(access_token)}")

        # Example MCP response structure
        result = {
            "success": True,
            "operation": operation,
            "data": kwargs
        }
        print(f"{Fore.GREEN}[MCP PROXY] ✅ Returning mock response")
        print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
        return result

    except CalendarServiceError as e:
        print(f"{Fore.RED}[MCP PROXY] ❌ CalendarServiceError: {e}")
        print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
        raise
    except Exception as e:
        error_msg = f"Calendar MCP error: {str(e)}"
        print(f"{Fore.RED}[MCP PROXY] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        print(f"{Fore.CYAN}[MCP PROXY] ═══════════════════════════════════════════════════════════")
        raise CalendarServiceError(error_msg)


# ============================================================================
# DUMMY CALENDAR IMPLEMENTATION
# ============================================================================

def get_dummy_available_slots(date_str: str) -> List[Dict[str, Any]]:
    """
    Generate dummy available appointment slots for testing.

    SPECIAL RULES:
    - Monday 2/9/2026: NO availability (completely booked)
    - Other weekdays: 6 slots (09:00-16:00)
    - Weekends: No availability

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        list: Available time slots
    """
    try:
        from datetime import datetime
        print(f"{Fore.YELLOW}[CALENDAR] get_dummy_available_slots() called with date={date_str}")

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        print(f"{Fore.YELLOW}[CALENDAR] Parsed date: {date_str} ({day_name})")

        # SPECIAL: Monday 2/9/2026 has NO availability
        if date_str == "2026-02-09":
            print(f"{Fore.YELLOW}[CALENDAR] ⚠️  Special rule: Monday 2/9/2026 has NO availability")
            return []

        # Weekends: no availability
        if day_name in ["Saturday", "Sunday"]:
            print(f"{Fore.YELLOW}[CALENDAR] ⚠️  Weekend ({day_name}): No availability")
            return []

        # Weekdays: standard slots
        available_slots = [
            {"date": date_str, "time": "09:00", "duration_minutes": 30},
            {"date": date_str, "time": "10:00", "duration_minutes": 30},
            {"date": date_str, "time": "11:00", "duration_minutes": 30},
            {"date": date_str, "time": "14:00", "duration_minutes": 30},
            {"date": date_str, "time": "15:00", "duration_minutes": 30},
            {"date": date_str, "time": "16:00", "duration_minutes": 30},
        ]

        print(f"{Fore.GREEN}[CALENDAR] ✅ Returning {len(available_slots)} available slots for {day_name}")
        for slot in available_slots:
            print(f"{Fore.GREEN}[CALENDAR]   • {slot['time']} ({slot['duration_minutes']} min)")

        return available_slots

    except Exception as e:
        print(f"{Fore.RED}[CALENDAR] ❌ Error generating dummy slots: {e}")
        import traceback
        traceback.print_exc()
        return []


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
    print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
    print(f"{Fore.MAGENTA}[TOOL CALL] check_availability() called from ElevenLabs agent")
    print(f"{Fore.MAGENTA}[TOOL CALL] Parameters: user_id={user_id}, date={date}, time={time}")

    try:
        # TODO: Parse natural language date ("next Tuesday", etc.)
        parsed_date = date  # For now, assume YYYY-MM-DD format
        print(f"{Fore.MAGENTA}[TOOL CALL] Parsed date: {parsed_date}")

        # Call Calendar MCP to get available slots
        print(f"{Fore.MAGENTA}[TOOL CALL] Calling call_calendar_mcp()...")
        result = call_calendar_mcp(
            user_id=user_id,
            db=db,
            operation="get_available_slots",
            date=parsed_date,
            duration_minutes=config.APPOINTMENT_DURATION_MINUTES,
            buffer_minutes=config.APPOINTMENT_BUFFER_MINUTES
        )

        if not result["success"]:
            print(f"{Fore.RED}[TOOL CALL] ❌ call_calendar_mcp returned success=False")
            return {
                "success": False,
                "error": "Could not check calendar availability"
            }

        print(f"{Fore.MAGENTA}[TOOL CALL] ✅ Getting dummy slots...")

        # DUMMY CALENDAR IMPLEMENTATION
        # Returns mock available slots based on date
        available_slots = get_dummy_available_slots(parsed_date)

        response = {
            "success": True,
            "date": parsed_date,
            "available_slots": available_slots
        }

        print(f"{Fore.GREEN}[TOOL CALL] ✅ Returning {len(available_slots)} slots to ElevenLabs")
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return response

    except CalendarServiceError as e:
        print(f"{Fore.RED}[TOOL CALL] ❌ CalendarServiceError: {e}")
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        print(f"{Fore.RED}[TOOL CALL] ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
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
    print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
    print(f"{Fore.MAGENTA}[TOOL CALL] book_appointment() called from ElevenLabs agent")
    print(f"{Fore.MAGENTA}[TOOL CALL] Parameters: user_id={user_id}, patient_name={patient_name}, phone={patient_phone}")
    print(f"{Fore.MAGENTA}[TOOL CALL]             date={date}, time={time}, type={appointment_type}")

    try:
        # Get doctor user
        print(f"{Fore.MAGENTA}[TOOL CALL] Looking up doctor user (user_id={user_id})...")
        doctor = auth_service.get_user_by_id(db, user_id)
        if not doctor:
            print(f"{Fore.RED}[TOOL CALL] ❌ Doctor not found (user_id={user_id})")
            print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
            return {
                "success": False,
                "error": "Doctor not found"
            }
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Doctor found: {doctor.email}")

        # Find or create patient
        print(f"{Fore.MAGENTA}[TOOL CALL] Looking up patient (phone={patient_phone})...")
        patient = db.query(database.Patient).filter(
            database.Patient.doctor_id == user_id,
            database.Patient.phone == patient_phone
        ).first()

        if not patient:
            print(f"{Fore.MAGENTA}[TOOL CALL] Patient not found, creating new patient...")
            patient_id = f"pat_{__import__('uuid').uuid4().hex[:12]}"
            patient = database.Patient(
                id=patient_id,
                doctor_id=user_id,
                name=patient_name,
                phone=patient_phone
            )
            db.add(patient)
            db.flush()
            print(f"{Fore.GREEN}[TOOL CALL] ✅ New patient created: {patient_id}")
        else:
            print(f"{Fore.GREEN}[TOOL CALL] ✅ Existing patient found: {patient.id}")

        # Create calendar event via Calendar MCP
        print(f"{Fore.MAGENTA}[TOOL CALL] Creating calendar event via call_calendar_mcp()...")
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
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Calendar event created")

        # TODO: Extract calendar event ID from calendar_result
        calendar_event_id = calendar_result.get("event_id")
        print(f"{Fore.MAGENTA}[TOOL CALL] Calendar event ID: {calendar_event_id}")

        # Create appointment record in database
        print(f"{Fore.MAGENTA}[TOOL CALL] Creating appointment record in database...")
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
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Appointment record created: {appointment_id}")

        # TODO: Send SMS confirmation via Twilio
        # twilio.send_sms(
        #     to_number=patient_phone,
        #     message=f"Hi {patient_name}, your appointment is confirmed for {date} at {time}. Reply STOP to opt out."
        # )

        confirmation_number = f"CP-{date.replace('-', '')}-{appointment_id[:3].upper()}"

        if config.DEBUG:
            print(f"{Fore.GREEN}[DEBUG] Appointment created: {appointment_id}")

        response = {
            "success": True,
            "appointment_id": appointment_id,
            "confirmation_number": confirmation_number,
            "message": f"Appointment confirmed for {patient_name} on {date} at {time}. Confirmation number: {confirmation_number}"
        }
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Returning success response to ElevenLabs")
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return response

    except Exception as e:
        error_msg = f"Failed to book appointment: {str(e)}"
        print(f"{Fore.RED}[TOOL CALL] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        db.rollback()
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
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
    print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
    print(f"{Fore.MAGENTA}[TOOL CALL] cancel_appointment() called from ElevenLabs agent")
    print(f"{Fore.MAGENTA}[TOOL CALL] Parameters: user_id={user_id}, appointment_id={appointment_id}")

    try:
        # Look up appointment
        print(f"{Fore.MAGENTA}[TOOL CALL] Looking up appointment (id={appointment_id})...")
        appointment = db.query(database.Appointment).filter(
            database.Appointment.id == appointment_id,
            database.Appointment.doctor_id == user_id
        ).first()

        if not appointment:
            print(f"{Fore.RED}[TOOL CALL] ❌ Appointment not found (id={appointment_id})")
            print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
            return {
                "success": False,
                "error": "Appointment not found"
            }
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Appointment found: {appointment_id} (status={appointment.status})")

        # Delete calendar event via Calendar MCP
        if appointment.calendar_event_id:
            print(f"{Fore.MAGENTA}[TOOL CALL] Deleting calendar event (event_id={appointment.calendar_event_id})...")
            call_calendar_mcp(
                user_id=user_id,
                db=db,
                operation="delete_event",
                event_id=appointment.calendar_event_id
            )
            print(f"{Fore.GREEN}[TOOL CALL] ✅ Calendar event deleted")
        else:
            print(f"{Fore.YELLOW}[TOOL CALL] ⚠️  No calendar event ID to delete")

        # Update appointment status
        print(f"{Fore.MAGENTA}[TOOL CALL] Updating appointment status to 'cancelled'...")
        appointment.status = "cancelled"
        appointment.updated_at = datetime.utcnow()
        db.commit()
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Appointment status updated")

        # TODO: Send cancellation SMS to patient

        if config.DEBUG:
            print(f"{Fore.GREEN}[DEBUG] Appointment cancelled: {appointment_id}")

        response = {
            "success": True,
            "message": "Appointment cancelled"
        }
        print(f"{Fore.GREEN}[TOOL CALL] ✅ Returning success response to ElevenLabs")
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return response

    except Exception as e:
        error_msg = f"Failed to cancel appointment: {str(e)}"
        print(f"{Fore.RED}[TOOL CALL] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        db.rollback()
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
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
    print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
    print(f"{Fore.MAGENTA}[TOOL CALL] get_upcoming_appointments() called from ElevenLabs agent")
    print(f"{Fore.MAGENTA}[TOOL CALL] Parameters: user_id={user_id}, days_ahead={days_ahead}")

    try:
        # Query upcoming appointments from database
        print(f"{Fore.MAGENTA}[TOOL CALL] Calculating future date cutoff...")
        future_date = (datetime.utcnow() + timedelta(days=days_ahead)).date()
        print(f"{Fore.MAGENTA}[TOOL CALL] Looking up appointments through {future_date.isoformat()}...")

        appointments = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == user_id,
            database.Appointment.date <= future_date.isoformat(),
            database.Appointment.status.in_(["scheduled", "confirmed"])
        ).order_by(database.Appointment.date, database.Appointment.time).all()

        print(f"{Fore.GREEN}[TOOL CALL] ✅ Found {len(appointments)} upcoming appointments")
        for appt in appointments:
            print(f"{Fore.GREEN}[TOOL CALL]   • {appt.date} {appt.time} - {appt.patient.name} ({appt.status})")

        result = [
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

        print(f"{Fore.GREEN}[TOOL CALL] ✅ Returning {len(result)} appointments to ElevenLabs")
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return result

    except Exception as e:
        error_msg = f"Failed to get appointments: {str(e)}"
        print(f"{Fore.RED}[TOOL CALL] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        print(f"{Fore.MAGENTA}[TOOL CALL] ═══════════════════════════════════════════════════════════")
        return []
