"""
CallPilot Backend API

Main FastAPI application with endpoints for:
- Doctor authentication
- Patient management
- Appointment scheduling
- Call management
- Google Calendar integration
- Dashboard and settings
"""

import sys
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer
from urllib.parse import urlencode
from starlette.authentication import AuthCredentials, SimpleUser
from colorama import Fore, init

from src import config
from src.core import models
from src.database import models as db_models, SessionLocal, init_db, get_db, Session
from src.auth import service as auth_service
from src.calendar import service as calendar_service
from src.integrations.twilio import TwilioWrapper, TwilioCallError

init(autoreset=True)

OAUTH_REDIRECT_PARAM_ACCESS_TOKEN = "access_token"
OAUTH_REDIRECT_PARAM_REFRESH_TOKEN = "refresh_token"
OAUTH_REDIRECT_PARAM_TOKEN_TYPE = "token_type"
OAUTH_REDIRECT_PARAM_EXPIRES_IN = "expires_in"
OAUTH_REDIRECT_PARAM_USER_ID = "user_id"
OAUTH_REDIRECT_QUERY_SEPARATOR = "?"
OAUTH_REDIRECT_APPEND_SEPARATOR = "&"
OAUTH_TOKEN_TYPE_BEARER = "bearer"


def build_oauth_redirect_url(base_url: str, payload: dict) -> str:
    """Build OAuth redirect URL with encoded query parameters."""
    query_string = urlencode(payload)
    separator = (
        OAUTH_REDIRECT_APPEND_SEPARATOR
        if OAUTH_REDIRECT_QUERY_SEPARATOR in base_url
        else OAUTH_REDIRECT_QUERY_SEPARATOR
    )
    return f"{base_url}{separator}{query_string}"

# ============================================================================
# APPLICATION SETUP
# ============================================================================

# Validate configuration on startup
try:
    config.validate_config()
except config.ConfigError as e:
    print(f"{Fore.RED}❌ Configuration validation failed: {e}")
    sys.exit(1)

# Initialize database
try:
    init_db()
    print(f"{Fore.GREEN}✅ Database initialized")
except Exception as e:
    print(f"{Fore.RED}❌ Database initialization failed: {e}")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    debug=config.DEBUG
)

# Initialize Twilio wrapper
try:
    twilio = TwilioWrapper()
except TwilioCallError as e:
    print(f"{Fore.RED}❌ Twilio initialization failed: {e}")
    sys.exit(1)

# HTTP Bearer security for JWT tokens
security = HTTPBearer()

print(f"{Fore.GREEN}✅ {config.APP_NAME} API initialized")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> str:
    """
    Extract and validate JWT token from Authorization header.

    Returns:
        str: User ID if valid token
    """
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims"
        )

    return user_id


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "timestamp": datetime.utcnow()
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS (/api/auth)
# ============================================================================

@app.get("/api/auth/google/url", response_model=models.CalendarAuthUrl)
async def get_google_auth_url(db: Session = Depends(get_db)):
    """
    Get Google OAuth authorization URL for doctor login.

    Frontend flow:
    1. User clicks "Login with Google"
    2. Frontend calls this endpoint → Gets auth URL
    3. Frontend redirects to Google OAuth
    4. User authenticates with Google
    5. Google redirects to /api/auth/google/callback with code
    6. Backend exchanges code for token and creates session

    Returns:
        auth_url: URL to redirect user to Google OAuth
        state: State token to prevent CSRF
    """
    try:
        auth_url, state = auth_service.get_google_oauth_url()
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auth URL: {str(e)}"
        )


@app.post("/api/auth/google/callback")
async def google_oauth_callback(
    request: models.CalendarCallback,
    db: Session = Depends(get_db)
):
    return handle_google_oauth_callback(request.code, request.state, db)


@app.get("/api/auth/google/callback")
async def google_oauth_callback_get(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    return handle_google_oauth_callback(code, state, db)


def handle_google_oauth_callback(code: str, state: str, db: Session):
    """
    Handle Google OAuth callback.

    Backend Proxy Pattern - Step 1: Store OAuth Token
    1. User authorizes, Google redirects with code
    2. Backend exchanges code for OAuth token
    3. Stores token in database (encrypted)
    4. Creates JWT session tokens

    This is where the user's Google Calendar access is granted to our backend.
    From this point on, we can call Calendar MCP with user's token via the proxy.

    Args:
        code: Authorization code from Google
        state: State token for CSRF protection

    Returns:
        access_token: JWT token for API access
        refresh_token: Token for refreshing access_token
        user_id: User ID for reference
    """
    try:
        # Exchange Google auth code for OAuth token
        oauth_token = auth_service.exchange_oauth_code_for_token(
            code,
            state
        )

        if not oauth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code"
            )

        # Get user info from Google
        user_info = auth_service.get_user_info_from_google(
            oauth_token["access_token"]
        )

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info from Google"
            )

        # Create or update user with OAuth token
        user = auth_service.create_or_update_user(
            db=db,
            email=user_info["email"],
            name=user_info.get("name", ""),
            oauth_token_data=oauth_token
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

        # Create session with JWT tokens
        session = auth_service.create_session(db, user.id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )

        response_payload = {
            OAUTH_REDIRECT_PARAM_ACCESS_TOKEN: session.access_token,
            OAUTH_REDIRECT_PARAM_REFRESH_TOKEN: session.refresh_token,
            OAUTH_REDIRECT_PARAM_TOKEN_TYPE: OAUTH_TOKEN_TYPE_BEARER,
            OAUTH_REDIRECT_PARAM_EXPIRES_IN: config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            OAUTH_REDIRECT_PARAM_USER_ID: user.id
        }

        if config.FRONTEND_OAUTH_REDIRECT_URL:
            redirect_url = build_oauth_redirect_url(
                config.FRONTEND_OAUTH_REDIRECT_URL,
                response_payload
            )
            return RedirectResponse(url=redirect_url)

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


# ============================================================================
# DOCTOR ENDPOINTS (/api/doctors)
# ============================================================================

@app.get("/api/doctors/me", response_model=models.DoctorProfile)
async def get_doctor_profile():
    """
    Get current doctor's profile

    TODO: Extract doctor ID from JWT token
    TODO: Fetch profile from database
    """
    return {
        "id": "doc_placeholder",
        "email": config.DOCTOR_EMAIL,
        "name": "Dr. Placeholder",
        "phone": "+1234567890",
        "timezone": config.DOCTOR_TIMEZONE,
        "calendar_connected": False,
        "created_at": datetime.utcnow()
    }


# ============================================================================
# CALENDAR ENDPOINTS (/api/calendar)
# ============================================================================
#
# These endpoints implement the Backend Proxy Pattern (Option 2):
# - User authenticates with Google OAuth (stores token in DB)
# - ElevenLabs agent calls these endpoints with user_id in context
# - Backend looks up user's OAuth token
# - Backend calls Calendar MCP with that token
# - Results returned to agent
#

@app.get("/api/calendar/status", response_model=models.CalendarStatus)
async def get_calendar_status(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current calendar connection status.

    Checks if user has valid Google OAuth token (whether they've
    successfully authenticated with Google).

    Returns:
        connected: True if user has valid OAuth token
        calendar_id: User's Google Calendar ID if connected
        email: User's Google email if connected
        connected_at: Timestamp of when calendar was connected
    """
    try:
        user = auth_service.get_user_by_id(db, current_user)
        if not user:
            return {
                "connected": False,
                "calendar_id": None,
                "email": None,
                "connected_at": None
            }

        oauth_token = auth_service.get_user_oauth_token(db, current_user)
        connected = oauth_token is not None

        return {
            "connected": connected,
            "calendar_id": user.google_calendar_id,
            "email": user.email,
            "connected_at": user.created_at if connected else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar status: {str(e)}"
        )


@app.post("/api/calendar/disconnect")
async def disconnect_calendar(
    request: models.CalendarDisconnect,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Google Calendar.

    Revokes the OAuth token and removes calendar access.
    """
    try:
        user = auth_service.get_user_by_id(db, current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Clear OAuth tokens
        user.google_oauth_token = None
        user.google_refresh_token = None
        user.google_token_expiry = None
        db.commit()

        return {"success": True, "message": config.ERROR_CALENDAR_DISCONNECT}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect calendar: {str(e)}"
        )


@app.post("/api/calendar/check-availability", response_model=models.AvailabilityResponse)
async def check_availability_endpoint(
    request: models.AvailabilityRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check available appointment slots for a given date.

    Backend Proxy Pattern in Action:
    - ElevenLabs agent calls this with user_id in JWT token
    - We look up user's OAuth token from database
    - Call Calendar MCP with that token to check availability
    - Return available slots to agent

    This endpoint is called by the ElevenLabs agent during the booking conversation.
    The agent passes the date and we return available time slots.

    Args:
        date: Date to check (YYYY-MM-DD or natural language like "next Tuesday")

    Returns:
        success: True if check succeeded
        date: Normalized date
        available_slots: List of available times
    """
    try:
        result = calendar_service.check_availability(
            user_id=current_user,
            db=db,
            date=request.date
        )

        if not result["success"]:
            return {
                "success": False,
                "date": request.date,
                "error": result.get("error", "Failed to check availability")
            }

        return result

    except Exception as e:
        return {
            "success": False,
            "date": request.date,
            "error": f"Calendar check failed: {str(e)}"
        }


# ============================================================================
# PATIENT ENDPOINTS (/api/patients)
# ============================================================================

@app.get("/api/patients", response_model=List[models.PatientResponse])
async def list_patients(skip: int = 0, limit: int = 100):
    """
    List all patients

    TODO: Fetch from database with pagination
    """
    return []


@app.post("/api/patients", response_model=models.PatientResponse)
async def create_patient(request: models.PatientCreate):
    """
    Create new patient record

    TODO: Validate phone number format
    TODO: Store in database
    """
    return {
        "id": "pat_placeholder",
        "name": request.name,
        "phone": request.phone,
        "email": request.email,
        "notes": request.notes,
        "created_at": datetime.utcnow(),
        "last_appointment": None
    }


@app.get("/api/patients/{patient_id}", response_model=models.PatientResponse)
async def get_patient(patient_id: str):
    """
    Get patient details

    TODO: Fetch from database
    """
    return {
        "id": patient_id,
        "name": "Patient Name",
        "phone": "+1234567890",
        "email": "patient@example.com",
        "notes": None,
        "created_at": datetime.utcnow(),
        "last_appointment": None
    }


@app.put("/api/patients/{patient_id}", response_model=models.PatientResponse)
async def update_patient(patient_id: str, request: models.PatientUpdate):
    """
    Update patient record

    TODO: Validate input
    TODO: Update database
    """
    return {
        "id": patient_id,
        "name": request.name or "Patient Name",
        "phone": request.phone or "+1234567890",
        "email": request.email,
        "notes": request.notes,
        "created_at": datetime.utcnow(),
        "last_appointment": None
    }


@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """
    Delete patient record

    TODO: Soft delete from database (archive instead of remove)
    """
    return {"success": True, "message": f"Patient {patient_id} deleted"}


# ============================================================================
# APPOINTMENT ENDPOINTS (/api/appointments)
# ============================================================================

@app.get("/api/appointments", response_model=List[models.AppointmentResponse])
async def list_appointments(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all appointments for the authenticated doctor.
    """
    try:
        appointments = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == current_user
        ).offset(skip).limit(limit).all()

        return [
            {
                "id": appt.id,
                "calendar_event_id": appt.calendar_event_id,
                "patient_id": appt.patient_id,
                "patient_name": appt.patient.name,
                "date": appt.date,
                "time": appt.time,
                "duration_minutes": appt.duration_minutes,
                "type": appt.type,
                "status": appt.status,
                "notes": appt.notes,
                "reminder_sent": appt.reminder_sent,
                "created_at": appt.created_at
            }
            for appt in appointments
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list appointments: {str(e)}"
        )


@app.get("/api/appointments/upcoming", response_model=models.UpcomingAppointmentsResponse)
async def get_upcoming_appointments(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming appointments for the next 30 days.

    Uses Calendar MCP through backend proxy pattern.
    """
    try:
        appointments = calendar_service.get_upcoming_appointments(
            user_id=current_user,
            db=db,
            days_ahead=30
        )

        return {
            "count": len(appointments),
            "appointments": appointments
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upcoming appointments: {str(e)}"
        )


@app.post("/api/appointments", response_model=models.AppointmentResponse)
async def create_appointment(
    request: models.AppointmentCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new appointment.

    Backend Proxy Pattern in Action:
    - ElevenLabs agent calls this after patient confirms booking
    - We look up user's OAuth token from database
    - Create Calendar event via Calendar MCP with that token
    - Store appointment in database
    - Send SMS confirmation via Twilio
    - Return confirmation to agent

    Called by ElevenLabs agent tool: book_appointment
    """
    try:
        # For inbound calls from agent, patient details are in request
        # For API calls, patient_id is provided
        if request.patient_id:
            patient = db.query(database.Patient).filter(
                database.Patient.id == request.patient_id
            ).first()

            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Patient not found"
                )

            result = calendar_service.book_appointment(
                user_id=current_user,
                db=db,
                patient_name=patient.name,
                patient_phone=patient.phone,
                date=request.date,
                time=request.time,
                appointment_type=request.type or "General Checkup"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID required"
            )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to book appointment")
            )

        # Get created appointment from database
        appointment = db.query(database.Appointment).filter(
            database.Appointment.id == result["appointment_id"]
        ).first()

        return {
            "id": appointment.id,
            "calendar_event_id": appointment.calendar_event_id,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient.name,
            "date": appointment.date,
            "time": appointment.time,
            "duration_minutes": appointment.duration_minutes,
            "type": appointment.type,
            "status": appointment.status,
            "notes": appointment.notes,
            "reminder_sent": appointment.reminder_sent,
            "created_at": appointment.created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )


@app.put("/api/appointments/{appointment_id}", response_model=models.AppointmentResponse)
async def update_appointment(appointment_id: str, request: models.AppointmentUpdate):
    """
    Update appointment

    TODO: Update Google Calendar event
    TODO: Update database
    """
    return {
        "id": appointment_id,
        "calendar_event_id": None,
        "patient_id": "pat_placeholder",
        "patient_name": "Patient Name",
        "date": request.date or "2026-02-15",
        "time": request.time or "14:00",
        "duration_minutes": config.APPOINTMENT_DURATION_MINUTES,
        "type": request.type or "General Checkup",
        "status": request.status or "scheduled",
        "notes": request.notes,
        "reminder_sent": False,
        "created_at": datetime.utcnow()
    }


@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """
    Delete/cancel appointment

    TODO: Delete from Google Calendar
    TODO: Update database
    TODO: Notify patient via SMS
    """
    return {"success": True, "message": f"Appointment {appointment_id} cancelled"}


@app.post("/api/appointments/{appointment_id}/confirm")
async def confirm_appointment(appointment_id: str, request: models.AppointmentConfirm):
    """
    Confirm appointment (patient callback from reminder)

    TODO: Update appointment status in database
    TODO: Update Google Calendar event
    """
    return {"success": True, "message": "Appointment confirmed"}


# ============================================================================
# CALL ENDPOINTS (/api/calls)
# ============================================================================

@app.get("/api/calls", response_model=List[models.CallResponse])
async def list_calls(skip: int = 0, limit: int = 100):
    """
    List all calls (inbound and outbound)

    TODO: Fetch from database with pagination
    """
    return []


@app.get("/api/calls/scheduled", response_model=models.ScheduledCallsResponse)
async def get_scheduled_calls():
    """
    Get scheduled outbound calls

    TODO: Query database for upcoming calls
    """
    return {"count": 0, "calls": []}


@app.get("/api/calls/{call_id}", response_model=models.CallResponse)
async def get_call(call_id: str):
    """
    Get call details

    TODO: Fetch from database and Twilio
    """
    return {
        "id": call_id,
        "call_sid": "CA" + call_id,
        "patient_id": "pat_placeholder",
        "patient_name": "Patient Name",
        "phone": "+1234567890",
        "type": "reminder",
        "status": "completed",
        "duration_seconds": 120,
        "started_at": datetime.utcnow(),
        "ended_at": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }


@app.post("/api/calls/manual", response_model=models.CallResponse)
async def make_manual_call(request: models.CallCreate):
    """
    Manually initiate outbound call to patient

    TODO: Validate patient exists
    TODO: Initiate Twilio call
    TODO: Store in database
    """
    try:
        result = twilio.make_outbound_call(
            to_number="+1234567890",  # TODO: Get from patient
            twiml_url=config.WEBHOOK_URL
        )
        return {
            "id": "call_placeholder",
            "call_sid": result["call_sid"],
            "patient_id": request.patient_id,
            "patient_name": "Patient Name",
            "phone": "+1234567890",
            "type": request.call_type or "manual",
            "status": result["status"],
            "duration_seconds": 0,
            "started_at": datetime.utcnow(),
            "ended_at": None,
            "created_at": datetime.utcnow()
        }
    except TwilioCallError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=config.ERROR_CALL_FAILED
        )


# ============================================================================
# DASHBOARD ENDPOINTS (/api/dashboard)
# ============================================================================

@app.get("/api/dashboard/stats", response_model=models.DashboardStats)
async def get_dashboard_stats():
    """
    Get dashboard statistics

    TODO: Calculate from database
    """
    return {
        "total_patients": 0,
        "total_appointments": 0,
        "upcoming_appointments": 0,
        "completed_appointments": 0,
        "no_show_count": 0,
        "total_calls_made": 0,
        "successful_calls": 0
    }


@app.get("/api/dashboard/activity", response_model=models.DashboardActivity)
async def get_dashboard_activity():
    """
    Get recent activity (appointments, calls, upcoming events)

    TODO: Query database for recent records
    """
    return {
        "recent_appointments": [],
        "recent_calls": [],
        "upcoming_events": []
    }


# ============================================================================
# SETTINGS ENDPOINTS (/api/settings)
# ============================================================================

@app.get("/api/settings", response_model=models.SettingsResponse)
async def get_settings():
    """
    Get application settings

    TODO: Fetch from database (per doctor)
    """
    return {
        "appointment_duration_minutes": config.APPOINTMENT_DURATION_MINUTES,
        "reminder_hours_before": config.REMINDER_HOURS_BEFORE,
        "timezone": config.DOCTOR_TIMEZONE,
        "enable_sms_confirmations": config.ENABLE_SMS_CONFIRMATIONS,
        "enable_reminders": config.ENABLE_REMINDERS,
        "enable_outbound_calls": config.ENABLE_OUTBOUND_CALLS
    }


@app.put("/api/settings", response_model=models.SettingsResponse)
async def update_settings(request: models.SettingsUpdate):
    """
    Update application settings

    TODO: Validate input
    TODO: Update database
    TODO: Restart scheduler if reminder settings changed
    """
    return {
        "appointment_duration_minutes": request.appointment_duration_minutes or config.APPOINTMENT_DURATION_MINUTES,
        "reminder_hours_before": request.reminder_hours_before or config.REMINDER_HOURS_BEFORE,
        "timezone": request.timezone or config.DOCTOR_TIMEZONE,
        "enable_sms_confirmations": request.enable_sms_confirmations if request.enable_sms_confirmations is not None else config.ENABLE_SMS_CONFIRMATIONS,
        "enable_reminders": request.enable_reminders if request.enable_reminders is not None else config.ENABLE_REMINDERS,
        "enable_outbound_calls": config.ENABLE_OUTBOUND_CALLS
    }


# ============================================================================
# WEBHOOK ENDPOINTS (/api/webhooks)
# ============================================================================

@app.post("/api/webhooks/elevenlabs")
async def elevenlabs_webhook(payload: models.ElevenLabsWebhookPayload):
    """
    Webhook for ElevenLabs call events

    Handles:
    - Inbound call routing
    - Outbound call status updates
    - Agent interaction events

    TODO: Process different event types
    TODO: Update call records in database
    TODO: Trigger appropriate actions (SMS, reminders, etc.)
    """
    if config.DEBUG:
        print(f"{Fore.CYAN}[DEBUG] ElevenLabs webhook received: {payload.call_id}")

    return {
        "success": True,
        "message": "Webhook processed"
    }


# ============================================================================
# TWILIO VOICE WEBHOOK
# ============================================================================

@app.post("/api/webhooks/twilio/voice")
async def twilio_voice_webhook():
    """
    Webhook for Twilio voice events

    Handles inbound call routing to ElevenLabs agent.

    TODO: Parse Twilio request parameters
    TODO: Return appropriate TwiML response
    """
    response = twilio.handle_inbound_call(
        from_number="+1234567890",  # TODO: Get from Twilio request
        to_number=config.TWILIO_PHONE_NUMBER
    )
    return response.to_xml()


# ============================================================================
# ERROR HANDLING
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    print(f"{Fore.RED}❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Called when application starts"""
    print(f"{Fore.GREEN}✅ {config.APP_NAME} API started")
    print(f"{Fore.CYAN}📊 Debug mode: {config.DEBUG}")
    print(f"{Fore.CYAN}🔗 API Base URL: {config.API_BASE_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Called when application shuts down"""
    print(f"{Fore.YELLOW}⏹️  {config.APP_NAME} API shutting down")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print(f"{Fore.CYAN}Starting {config.APP_NAME} API...")
    print(f"{Fore.CYAN}Running on {config.API_BASE_URL}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
