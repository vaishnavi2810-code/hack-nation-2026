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
from datetime import datetime, timedelta, time
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from urllib.parse import urlencode
from starlette.authentication import AuthCredentials, SimpleUser
from colorama import Fore, init
from googleapiclient.discovery import build
import pytz

from src import config
from src.core import models
from src.database import models as database, SessionLocal, init_db, get_db, Session
from src.auth import service as auth_service
from src.calendar import service as calendar_service
from src.integrations.twilio import TwilioWrapper, TwilioCallError

init(autoreset=True)

OAUTH_REDIRECT_PARAM_ACCESS_TOKEN = "access_token"
OAUTH_REDIRECT_PARAM_REFRESH_TOKEN = "refresh_token"
OAUTH_REDIRECT_PARAM_TOKEN_TYPE = "token_type"
OAUTH_REDIRECT_PARAM_EXPIRES_IN = "expires_in"
OAUTH_REDIRECT_PARAM_USER_ID = "user_id"
OAUTH_REDIRECT_PARAM_ERROR = "error"
OAUTH_REDIRECT_PARAM_ERROR_DESCRIPTION = "error_description"
OAUTH_REDIRECT_QUERY_SEPARATOR = "?"
OAUTH_REDIRECT_APPEND_SEPARATOR = "&"
OAUTH_TOKEN_TYPE_BEARER = "bearer"
OAUTH_CALLBACK_ERROR_TEMPLATE = "OAuth callback failed: {error}"
OAUTH_ERROR_EXCHANGE_FAILED = "Failed to exchange authorization code"
OAUTH_ERROR_USERINFO_FAILED = "Failed to get user info from Google"
OAUTH_ERROR_CREATE_USER_FAILED = "Failed to create user account"
OAUTH_ERROR_CREATE_SESSION_FAILED = "Failed to create session"
OAUTH_ERROR_GENERIC = "Unable to complete Google sign-in"
ERROR_DOCTOR_NOT_FOUND = "Doctor account not found."
DEFAULT_DOCTOR_PHONE = ""
ERROR_CALENDAR_NOT_CONNECTED = "Calendar is not connected."
ERROR_CALENDAR_DATE_INVALID = "Invalid date. Use YYYY-MM-DD or 'today'."
ERROR_CALENDAR_FETCH_FAILED = "Failed to fetch calendar appointments."
ERROR_APPOINTMENT_NOT_FOUND = "Appointment not found."
ERROR_APPOINTMENT_NO_SHOW_FAILED = "Failed to mark appointment as no-show."
NO_SHOW_SUCCESS_MESSAGE = "Appointment marked as no-show."
CALENDAR_TIMEZONE_FALLBACK = "UTC"
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
CORS_ALLOW_CREDENTIALS = True
GOOGLE_CALENDAR_API_NAME = "calendar"
GOOGLE_CALENDAR_API_VERSION = "v3"
GOOGLE_CALENDAR_ORDER_BY = "startTime"
GOOGLE_CALENDAR_SINGLE_EVENTS = True
GOOGLE_CALENDAR_START_FIELD = "start"
GOOGLE_CALENDAR_DATE_TIME_FIELD = "dateTime"
GOOGLE_CALENDAR_DATE_FIELD = "date"
GOOGLE_CALENDAR_SUMMARY_FIELD = "summary"
GOOGLE_CALENDAR_DESCRIPTION_FIELD = "description"
GOOGLE_CALENDAR_STATUS_FIELD = "status"
GOOGLE_CALENDAR_STATUS_CANCELLED = "cancelled"
APPOINTMENT_SUMMARY_PREFIX = "Appointment:"
APPOINTMENT_SUMMARY_FALLBACK = "Appointment"
APPOINTMENT_STATUS_SCHEDULED = "scheduled"
APPOINTMENT_STATUS_CANCELLED = "cancelled"
APPOINTMENT_STATUS_NO_SHOW = "no_show"
APPOINTMENT_TYPE_FALLBACK = "General"
DESCRIPTION_FIELD_SEPARATOR = ": "
DESCRIPTION_FIELD_STATUS = "status"
DESCRIPTION_FIELD_TYPE = "type"
DESCRIPTION_KEY_SEPARATOR = " "
DESCRIPTION_KEY_REPLACEMENT = "_"
APPOINTMENT_TIME_ALL_DAY = "All day"
DATE_INPUT_FORMAT = "%Y-%m-%d"
DATE_OUTPUT_FORMAT = "%Y-%m-%d"
TIME_OUTPUT_FORMAT = "%H:%M"
DATE_QUERY_PARAM = "date"
DAYS_AHEAD_QUERY_PARAM = "days_ahead"
MAX_RESULTS_QUERY_PARAM = "max_results"
DATE_VALUE_TODAY = "today"
DATE_VALUE_TOMORROW = "tomorrow"
DATE_RANGE_DAYS = 1
DATETIME_UTC_SUFFIX = "Z"
DATETIME_UTC_OFFSET = "+00:00"


def build_oauth_redirect_url(base_url: str, payload: dict) -> str:
    """Build OAuth redirect URL with encoded query parameters."""
    query_string = urlencode(payload)
    separator = (
        OAUTH_REDIRECT_APPEND_SEPARATOR
        if OAUTH_REDIRECT_QUERY_SEPARATOR in base_url
        else OAUTH_REDIRECT_QUERY_SEPARATOR
    )
    return f"{base_url}{separator}{query_string}"


def parse_calendar_date(date_value: str, timezone: pytz.BaseTzInfo) -> datetime.date:
    """Parse a calendar date string into a date."""
    normalized = date_value.strip().lower()
    today = datetime.now(timezone).date()

    if normalized == DATE_VALUE_TODAY:
        return today
    if normalized == DATE_VALUE_TOMORROW:
        return today + timedelta(days=DATE_RANGE_DAYS)

    return datetime.strptime(normalized, DATE_INPUT_FORMAT).date()


def resolve_time_window(
    date_value: Optional[str],
    days_ahead: Optional[int],
    timezone: pytz.BaseTzInfo
) -> tuple[datetime, datetime]:
    """Resolve time window for calendar query."""
    now = datetime.now(timezone)

    if date_value:
        target_date = parse_calendar_date(date_value, timezone)
        day_start = timezone.localize(datetime.combine(target_date, time.min))
        day_end = day_start + timedelta(days=DATE_RANGE_DAYS)
        time_min = now if target_date == now.date() else day_start
        return time_min, day_end

    lookahead_days = days_ahead if days_ahead is not None else config.APPOINTMENTS_LOOKAHEAD_DAYS
    return now, now + timedelta(days=lookahead_days)


def normalize_summary(summary: Optional[str]) -> str:
    """Normalize Google Calendar event summary to a patient label."""
    if not summary:
        return APPOINTMENT_SUMMARY_FALLBACK

    trimmed = summary.strip()
    if trimmed.lower().startswith(APPOINTMENT_SUMMARY_PREFIX.lower()):
        without_prefix = trimmed[len(APPOINTMENT_SUMMARY_PREFIX):].strip()
        return without_prefix or APPOINTMENT_SUMMARY_FALLBACK

    return trimmed


def parse_description_fields(description: Optional[str]) -> Dict[str, str]:
    """Parse structured fields from event description."""
    if not description:
        return {}

    parsed: Dict[str, str] = {}
    for line in description.splitlines():
        if DESCRIPTION_FIELD_SEPARATOR not in line:
            continue
        key, value = line.split(DESCRIPTION_FIELD_SEPARATOR, 1)
        normalized_key = key.strip().lower().replace(DESCRIPTION_KEY_SEPARATOR, DESCRIPTION_KEY_REPLACEMENT)
        parsed[normalized_key] = value.strip()
    return parsed


def parse_event_datetime(value: Optional[str], timezone: pytz.BaseTzInfo) -> Optional[datetime]:
    """Parse Google event datetime into localized datetime."""
    if not value:
        return None
    normalized = value
    if normalized.endswith(DATETIME_UTC_SUFFIX):
        normalized = normalized.replace(DATETIME_UTC_SUFFIX, DATETIME_UTC_OFFSET, 1)
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return timezone.localize(parsed)
    return parsed.astimezone(timezone)


def map_event_to_appointment_record(
    event: dict,
    timezone: pytz.BaseTzInfo
) -> models.CalendarAppointmentRecord:
    """Map Google Calendar event to appointment record."""
    summary = normalize_summary(event.get(GOOGLE_CALENDAR_SUMMARY_FIELD))
    description = event.get(GOOGLE_CALENDAR_DESCRIPTION_FIELD)
    parsed_description = parse_description_fields(description)

    appointment_type = parsed_description.get(DESCRIPTION_FIELD_TYPE, APPOINTMENT_TYPE_FALLBACK)
    status = parsed_description.get(DESCRIPTION_FIELD_STATUS, APPOINTMENT_STATUS_SCHEDULED)

    google_status = event.get(GOOGLE_CALENDAR_STATUS_FIELD)
    if google_status == GOOGLE_CALENDAR_STATUS_CANCELLED:
        status = APPOINTMENT_STATUS_CANCELLED

    start_payload = event.get(GOOGLE_CALENDAR_START_FIELD, {})
    start_date_time = start_payload.get(GOOGLE_CALENDAR_DATE_TIME_FIELD)
    start_date = start_payload.get(GOOGLE_CALENDAR_DATE_FIELD)

    if start_date_time:
        start_dt = parse_event_datetime(start_date_time, timezone)
        date_label = start_dt.strftime(DATE_OUTPUT_FORMAT) if start_dt else ""
        time_label = start_dt.strftime(TIME_OUTPUT_FORMAT) if start_dt else APPOINTMENT_TIME_ALL_DAY
    elif start_date:
        date_label = start_date
        time_label = APPOINTMENT_TIME_ALL_DAY
    else:
        date_label = ""
        time_label = APPOINTMENT_TIME_ALL_DAY

    return models.CalendarAppointmentRecord(
        id=event.get("id", ""),
        patient_id=event.get("id"),
        patient_name=summary,
        date=date_label,
        time=time_label,
        type=appointment_type,
        status=status
    )

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
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
    return handle_google_oauth_callback(
        request.code,
        request.state,
        db,
        redirect_on_success=False,
        redirect_on_error=False
    )


@app.get("/api/auth/google/callback")
async def google_oauth_callback_get(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    return handle_google_oauth_callback(
        code,
        state,
        db,
        redirect_on_success=True,
        redirect_on_error=True
    )


def handle_google_oauth_callback(
    code: str,
    state: str,
    db: Session,
    redirect_on_success: bool,
    redirect_on_error: bool
):
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
                detail=OAUTH_ERROR_EXCHANGE_FAILED
            )

        # Get user info from Google
        user_info = auth_service.get_user_info_from_google(
            oauth_token["access_token"]
        )

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=OAUTH_ERROR_USERINFO_FAILED
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
                detail=OAUTH_ERROR_CREATE_USER_FAILED
            )

        # Create session with JWT tokens
        session = auth_service.create_session(db, user.id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=OAUTH_ERROR_CREATE_SESSION_FAILED
            )

        response_payload = {
            OAUTH_REDIRECT_PARAM_ACCESS_TOKEN: session.access_token,
            OAUTH_REDIRECT_PARAM_REFRESH_TOKEN: session.refresh_token,
            OAUTH_REDIRECT_PARAM_TOKEN_TYPE: OAUTH_TOKEN_TYPE_BEARER,
            OAUTH_REDIRECT_PARAM_EXPIRES_IN: config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            OAUTH_REDIRECT_PARAM_USER_ID: user.id
        }

        if redirect_on_success and config.FRONTEND_OAUTH_REDIRECT_URL:
            redirect_url = build_oauth_redirect_url(
                config.FRONTEND_OAUTH_REDIRECT_URL,
                response_payload
            )
            return RedirectResponse(url=redirect_url)

        return response_payload

    except HTTPException as exc:
        if redirect_on_error and config.FRONTEND_OAUTH_REDIRECT_URL:
            error_payload = {
                OAUTH_REDIRECT_PARAM_ERROR: OAUTH_ERROR_GENERIC,
                OAUTH_REDIRECT_PARAM_ERROR_DESCRIPTION: str(exc.detail)
            }
            redirect_url = build_oauth_redirect_url(
                config.FRONTEND_OAUTH_REDIRECT_URL,
                error_payload
            )
            return RedirectResponse(url=redirect_url)
        raise
    except Exception as e:
        if redirect_on_error and config.FRONTEND_OAUTH_REDIRECT_URL:
            error_payload = {
                OAUTH_REDIRECT_PARAM_ERROR: OAUTH_ERROR_GENERIC,
                OAUTH_REDIRECT_PARAM_ERROR_DESCRIPTION: str(e)
            }
            redirect_url = build_oauth_redirect_url(
                config.FRONTEND_OAUTH_REDIRECT_URL,
                error_payload
            )
            return RedirectResponse(url=redirect_url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=OAUTH_CALLBACK_ERROR_TEMPLATE.format(error=str(e))
        )


# ============================================================================
# DOCTOR ENDPOINTS (/api/doctors)
# ============================================================================

@app.get("/api/doctors/me", response_model=models.DoctorProfile)
async def get_doctor_profile(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current doctor's profile

    Fetch profile from database.
    """
    user = db.query(database.User).filter(
        database.User.id == current_user
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_DOCTOR_NOT_FOUND
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "phone": user.phone or DEFAULT_DOCTOR_PHONE,
        "timezone": user.timezone or config.DOCTOR_TIMEZONE,
        "calendar_connected": bool(user.google_oauth_token),
        "created_at": user.created_at
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
    - Frontend calls this with user_id in JWT token
    - We look up user's OAuth token from database
    - Call Calendar MCP with that token to check availability
    - Return available slots to frontend

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


@app.get("/api/calendar/appointments", response_model=List[models.CalendarAppointmentRecord])
async def list_calendar_appointments(
    date: Optional[str] = Query(None, alias=DATE_QUERY_PARAM),
    days_ahead: Optional[int] = Query(None, alias=DAYS_AHEAD_QUERY_PARAM),
    max_results: Optional[int] = Query(None, alias=MAX_RESULTS_QUERY_PARAM),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List appointments from the logged-in doctor's Google Calendar.
    """
    try:
        user = auth_service.get_user_by_id(db, current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_DOCTOR_NOT_FOUND
            )

        oauth_token = auth_service.get_user_oauth_token(db, current_user)
        if not oauth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_CALENDAR_NOT_CONNECTED
            )

        credentials = auth_service.build_google_credentials(oauth_token)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_CALENDAR_NOT_CONNECTED
            )

        tz_name = user.timezone or config.DOCTOR_TIMEZONE
        try:
            timezone = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            timezone = pytz.timezone(CALENDAR_TIMEZONE_FALLBACK)

        if days_ahead is not None and days_ahead <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_CALENDAR_DATE_INVALID
            )

        time_min, time_max = resolve_time_window(date, days_ahead, timezone)
        calendar_id = user.google_calendar_id or config.GOOGLE_CALENDAR_ID
        limit = max_results if max_results is not None else config.CALENDAR_MAX_RESULTS

        service = build(GOOGLE_CALENDAR_API_NAME, GOOGLE_CALENDAR_API_VERSION, credentials=credentials)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=limit,
            singleEvents=GOOGLE_CALENDAR_SINGLE_EVENTS,
            orderBy=GOOGLE_CALENDAR_ORDER_BY,
            timeZone=timezone.zone
        ).execute()

        events = result.get("items", [])
        return [map_event_to_appointment_record(event, timezone) for event in events]

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_CALENDAR_DATE_INVALID
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ERROR_CALENDAR_FETCH_FAILED} {str(e)}"
        )


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
    - Frontend calls this with user_id in JWT token
    - We look up user's OAuth token from database
    - Create Calendar event via Calendar MCP with that token
    - Store appointment in database
    - Send SMS confirmation via Twilio
    - Return confirmation to frontend

    Called by frontend appointment booking form
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

    TODO: Add JWT authentication
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

    TODO: Add JWT authentication
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


@app.post("/api/appointments/{appointment_id}/no-show")
async def mark_appointment_no_show(
    appointment_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an appointment as no-show.

    Updates Google Calendar event and local appointment record when available.
    """
    try:
        appointment = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == current_user,
            database.Appointment.id == appointment_id
        ).first()

        if not appointment:
            appointment = db.query(database.Appointment).filter(
                database.Appointment.doctor_id == current_user,
                database.Appointment.calendar_event_id == appointment_id
            ).first()

        calendar_event_id = appointment.calendar_event_id if appointment else appointment_id

        result = calendar_service.mark_no_show(calendar_event_id)
        if not result.get("success"):
            fallback_error = ERROR_APPOINTMENT_NOT_FOUND if not appointment else ERROR_APPOINTMENT_NO_SHOW_FAILED
            error_status = status.HTTP_404_NOT_FOUND if not appointment else status.HTTP_500_INTERNAL_SERVER_ERROR
            raise HTTPException(
                status_code=error_status,
                detail=result.get("error", fallback_error)
            )

        if appointment:
            appointment.status = APPOINTMENT_STATUS_NO_SHOW
            appointment.updated_at = datetime.utcnow()
            db.commit()

        return {
            "success": True,
            "message": NO_SHOW_SUCCESS_MESSAGE,
            "appointment_id": appointment.id if appointment else appointment_id,
            "status": APPOINTMENT_STATUS_NO_SHOW
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ERROR_APPOINTMENT_NO_SHOW_FAILED} {str(e)}"
        )


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
# ELEVENLABS AGENT ENDPOINTS (/api/agent)
# ============================================================================
# These endpoints are specifically for the ElevenLabs voice agent.
# They accept phone numbers instead of JWT, create patients dynamically,
# and return voice-appropriate responses with verbose logging.

class AgentCheckAvailabilityRequest(models.BaseModel):
    date: str

@app.post("/api/agent/calendar/availability")
async def agent_check_availability(
    request: AgentCheckAvailabilityRequest,
    db: Session = Depends(get_db)
):
    """
    Check available appointment slots for a given date.

    Called by ElevenLabs agent to show available times to patients.
    No authentication required (single-tenant prototype).

    Args:
        request: AgentCheckAvailabilityRequest with date

    Returns:
        available_slots: List of available times
    """
    date = request.date
    print(f"{Fore.CYAN}[AGENT API] check_availability called with date={date}")

    try:
        # Use hardcoded doctor_id for single-tenant
        doctor_id = "doctor_001"

        result = calendar_service.check_availability(
            user_id=doctor_id,
            db=db,
            date=date
        )

        print(f"{Fore.GREEN}[AGENT API] ✅ check_availability returned: {len(result.get('available_slots', []))} slots")
        return result

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "date": date,
            "error": str(e)
        }


class AgentListAppointmentsRequest(models.BaseModel):
    phone_number: str

@app.post("/api/agent/appointments/list")
async def agent_list_appointments(request: AgentListAppointmentsRequest, db: Session = Depends(get_db)):
    phone_number = request.phone_number
    """
    List all appointments for a patient by phone number.

    Called by ElevenLabs agent to retrieve patient's appointments.
    Matches patients by phone number.

    Args:
        phone_number: Patient's phone number (E.164 format)

    Returns:
        appointments: List of patient's appointments
    """
    print(f"{Fore.CYAN}[AGENT API] list_appointments called for phone={phone_number}")

    try:
        # Find patient by phone number
        patient = db.query(database.Patient).filter(
            database.Patient.phone == phone_number
        ).first()

        if not patient:
            print(f"{Fore.YELLOW}[AGENT API] ⚠️  Patient not found for phone={phone_number}")
            return {
                "success": True,
                "appointments": [],
                "message": f"No appointments found for this number"
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Found patient: {patient.id} ({patient.name})")

        # Get patient's appointments
        appointments = db.query(database.Appointment).filter(
            database.Appointment.patient_id == patient.id,
            database.Appointment.status.in_(["scheduled", "confirmed"])
        ).order_by(database.Appointment.date, database.Appointment.time).all()

        print(f"{Fore.GREEN}[AGENT API] ✅ Found {len(appointments)} appointments")

        return {
            "success": True,
            "patient_name": patient.name,
            "appointments": [
                {
                    "id": appt.id,
                    "date": appt.date,
                    "time": appt.time,
                    "type": appt.type,
                    "status": appt.status
                }
                for appt in appointments
            ]
        }

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


class AgentScheduleAppointmentRequest(models.BaseModel):
    phone_number: str
    patient_name: str
    date: str
    time: str
    appointment_type: str = "General Checkup"

@app.post("/api/agent/appointments/schedule")
async def agent_schedule_appointment(
    request: AgentScheduleAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a new appointment for a patient.

    Called by ElevenLabs agent after patient confirms booking.
    Creates patient if they don't exist.

    Args:
        request: AgentScheduleAppointmentRequest with patient and appointment details

    Returns:
        appointment_id: ID of created appointment
        confirmation_number: Human-readable confirmation
    """
    phone_number = request.phone_number
    patient_name = request.patient_name
    date = request.date
    time = request.time
    appointment_type = request.appointment_type

    print(f"{Fore.CYAN}[AGENT API] schedule_appointment called for phone={phone_number}, date={date}, time={time}")

    try:
        # Use hardcoded doctor_id for single-tenant
        doctor_id = "doctor_001"

        # Find or create patient
        patient = db.query(database.Patient).filter(
            database.Patient.phone == phone_number
        ).first()

        if not patient:
            print(f"{Fore.CYAN}[AGENT API] Creating new patient: {patient_name}")
            import uuid
            patient_id = f"pat_{uuid.uuid4().hex[:12]}"
            patient = database.Patient(
                id=patient_id,
                doctor_id=doctor_id,
                name=patient_name,
                phone=phone_number
            )
            db.add(patient)
            db.flush()
            print(f"{Fore.GREEN}[AGENT API] ✅ Created patient: {patient_id}")
        else:
            print(f"{Fore.GREEN}[AGENT API] ✅ Found existing patient: {patient.id}")

        # Book appointment using calendar service
        result = calendar_service.book_appointment(
            user_id=doctor_id,
            db=db,
            patient_name=patient.name,
            patient_phone=patient.phone,
            date=date,
            time=time,
            appointment_type=appointment_type
        )

        if not result["success"]:
            print(f"{Fore.RED}[AGENT API] ❌ booking failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", "Failed to book appointment")
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Appointment created: {result['appointment_id']}")
        return result

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


class AgentRescheduleAppointmentRequest(models.BaseModel):
    phone_number: str
    appointment_id: str
    new_date: str
    new_time: str

@app.post("/api/agent/appointments/reschedule")
async def agent_reschedule_appointment(
    request: AgentRescheduleAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Reschedule an existing appointment.

    Called by ElevenLabs agent when patient wants to change their appointment.

    Args:
        request: AgentRescheduleAppointmentRequest with reschedule details

    Returns:
        appointment_id: Updated appointment ID
        message: Confirmation message
    """
    phone_number = request.phone_number
    appointment_id = request.appointment_id
    new_date = request.new_date
    new_time = request.new_time

    print(f"{Fore.CYAN}[AGENT API] reschedule_appointment called for phone={phone_number}, appt={appointment_id}")
    print(f"{Fore.CYAN}[AGENT API]   New date/time: {new_date} {new_time}")

    try:
        # Verify patient owns this appointment
        patient = db.query(database.Patient).filter(
            database.Patient.phone == phone_number
        ).first()

        if not patient:
            print(f"{Fore.RED}[AGENT API] ❌ Patient not found")
            return {
                "success": False,
                "error": "Patient not found"
            }

        appointment = db.query(database.Appointment).filter(
            database.Appointment.id == appointment_id,
            database.Appointment.patient_id == patient.id
        ).first()

        if not appointment:
            print(f"{Fore.RED}[AGENT API] ❌ Appointment not found or doesn't belong to patient")
            return {
                "success": False,
                "error": "Appointment not found"
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Found appointment: {appointment.id}")

        # Update appointment
        old_date = appointment.date
        old_time = appointment.time

        appointment.date = new_date
        appointment.time = new_time
        appointment.updated_at = datetime.utcnow()
        db.commit()

        print(f"{Fore.GREEN}[AGENT API] ✅ Rescheduled from {old_date} {old_time} to {new_date} {new_time}")

        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": f"Your appointment has been rescheduled to {new_date} at {new_time}"
        }

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


class AgentCancelAppointmentRequest(models.BaseModel):
    phone_number: str
    appointment_id: str

@app.post("/api/agent/appointments/cancel")
async def agent_cancel_appointment(
    request: AgentCancelAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel an existing appointment.

    Called by ElevenLabs agent when patient wants to cancel.

    Args:
        request: AgentCancelAppointmentRequest with cancellation details

    Returns:
        success: True if cancelled
        message: Confirmation message
    """
    phone_number = request.phone_number
    appointment_id = request.appointment_id

    print(f"{Fore.CYAN}[AGENT API] cancel_appointment called for phone={phone_number}, appt={appointment_id}")

    try:
        # Verify patient owns this appointment
        patient = db.query(database.Patient).filter(
            database.Patient.phone == phone_number
        ).first()

        if not patient:
            print(f"{Fore.RED}[AGENT API] ❌ Patient not found")
            return {
                "success": False,
                "error": "Patient not found"
            }

        appointment = db.query(database.Appointment).filter(
            database.Appointment.id == appointment_id,
            database.Appointment.patient_id == patient.id
        ).first()

        if not appointment:
            print(f"{Fore.RED}[AGENT API] ❌ Appointment not found or doesn't belong to patient")
            return {
                "success": False,
                "error": "Appointment not found"
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Found appointment: {appointment.id}")

        # Cancel appointment using calendar service
        result = calendar_service.cancel_appointment(
            user_id="doctor_001",
            db=db,
            appointment_id=appointment_id
        )

        if not result["success"]:
            print(f"{Fore.RED}[AGENT API] ❌ Cancellation failed: {result.get('error')}")
            return result

        print(f"{Fore.GREEN}[AGENT API] ✅ Appointment cancelled")

        return {
            "success": True,
            "message": f"Your appointment on {appointment.date} at {appointment.time} has been cancelled"
        }

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


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
