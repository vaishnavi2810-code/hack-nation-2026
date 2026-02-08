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
from src.services.calendar_service import CalendarService
from src.core.auth import GoogleAuthManager
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
ERROR_CALENDAR_EVENT_UPDATE_FAILED = "Failed to update calendar event."
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
APPOINTMENT_SUMMARY_SEPARATOR = " "
APPOINTMENT_STATUS_SCHEDULED = "scheduled"
APPOINTMENT_STATUS_CANCELLED = "cancelled"
APPOINTMENT_STATUS_NO_SHOW = "no_show"
APPOINTMENT_TYPE_FALLBACK = "General"
SUMMARY_NO_SHOW_PREFIX = "NO SHOW:"
SUMMARY_NO_SHOW_FALLBACK = f"{SUMMARY_NO_SHOW_PREFIX}{APPOINTMENT_SUMMARY_SEPARATOR}{APPOINTMENT_SUMMARY_FALLBACK}"
DESCRIPTION_FIELD_SEPARATOR = ": "
DESCRIPTION_LABEL_STATUS = "Status"
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


def update_description_field(description: Optional[str], field_label: str, value: str) -> str:
    """Update or insert a field in the event description."""
    field_prefix = f"{field_label}{DESCRIPTION_FIELD_SEPARATOR}"
    if not description:
        return f"{field_label}{DESCRIPTION_FIELD_SEPARATOR}{value}"

    lines = description.splitlines()
    updated_lines: List[str] = []
    field_found = False

    for line in lines:
        if line.startswith(field_prefix):
            updated_lines.append(f"{field_label}{DESCRIPTION_FIELD_SEPARATOR}{value}")
            field_found = True
        else:
            updated_lines.append(line)

    if not field_found:
        updated_lines.append(f"{field_label}{DESCRIPTION_FIELD_SEPARATOR}{value}")

    return "\n".join(updated_lines)


def build_no_show_summary(summary: Optional[str]) -> str:
    """Build summary string for a no-show event."""
    if not summary:
        return SUMMARY_NO_SHOW_FALLBACK

    trimmed = summary.strip()
    if not trimmed:
        return SUMMARY_NO_SHOW_FALLBACK

    if trimmed.lower().startswith(SUMMARY_NO_SHOW_PREFIX.lower()):
        return trimmed

    if trimmed.lower().startswith(APPOINTMENT_SUMMARY_PREFIX.lower()):
        without_prefix = trimmed[len(APPOINTMENT_SUMMARY_PREFIX):].strip()
        patient_label = without_prefix or APPOINTMENT_SUMMARY_FALLBACK
        return f"{SUMMARY_NO_SHOW_PREFIX}{APPOINTMENT_SUMMARY_SEPARATOR}{patient_label}"

    return f"{SUMMARY_NO_SHOW_PREFIX}{APPOINTMENT_SUMMARY_SEPARATOR}{trimmed}"


def resolve_calendar_credentials(current_user: str, db: Session):
    """Resolve calendar credentials and user context."""
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

    calendar_id = user.google_calendar_id or config.GOOGLE_CALENDAR_ID
    return user, credentials, calendar_id


def update_calendar_event_no_show(
    *,
    event_id: str,
    calendar_id: str,
    credentials
) -> None:
    """Update Google Calendar event to no-show status."""
    service = build(GOOGLE_CALENDAR_API_NAME, GOOGLE_CALENDAR_API_VERSION, credentials=credentials)

    try:
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{ERROR_APPOINTMENT_NOT_FOUND} {str(e)}"
        )

    description = event.get(GOOGLE_CALENDAR_DESCRIPTION_FIELD, "")
    updated_description = update_description_field(description, DESCRIPTION_LABEL_STATUS, APPOINTMENT_STATUS_NO_SHOW)
    updated_summary = build_no_show_summary(event.get(GOOGLE_CALENDAR_SUMMARY_FIELD))

    event[GOOGLE_CALENDAR_DESCRIPTION_FIELD] = updated_description
    event[GOOGLE_CALENDAR_SUMMARY_FIELD] = updated_summary

    try:
        service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ERROR_CALENDAR_EVENT_UPDATE_FAILED} {str(e)}"
        )


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

# Initialize Calendar Service
try:
    cal_service = CalendarService()
    print(f"{Fore.GREEN}✅ Calendar Service initialized")
except Exception as e:
    print(f"{Fore.RED}❌ Calendar Service initialization failed: {e}")
    sys.exit(1)

# Initialize Google Auth Manager
try:
    google_auth = GoogleAuthManager()
    print(f"{Fore.GREEN}✅ Google Auth Manager initialized")
except Exception as e:
    print(f"{Fore.RED}❌ Google Auth Manager initialization failed: {e}")
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
    """
    print(f"{Fore.CYAN}[AUTH] GET /api/auth/google/url called")
    try:
        print(f"{Fore.CYAN}[AUTH] Calling google_auth.get_auth_url()...")
        auth_url = google_auth.get_auth_url()
        print(f"{Fore.GREEN}[AUTH] ✅ Successfully generated auth URL")
        print(f"{Fore.CYAN}[AUTH] Auth URL: {auth_url[:80]}...")
        return {
            "auth_url": auth_url,
            "state": ""
        }
    except Exception as e:
        print(f"{Fore.RED}[AUTH] ❌ Error generating auth URL: {str(e)}")
        import traceback
        print(f"{Fore.RED}[AUTH] Traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auth URL: {str(e)}"
        )


@app.post("/api/auth/google/callback")
async def google_oauth_callback(
    request: models.CalendarCallback,
    db: Session = Depends(get_db)
):

    print(f"{Fore.CYAN}[AUTH] POST /api/auth/google/callback received")
    print(f"{Fore.CYAN}[AUTH]   Code (first 20 chars): {request.code[:20] if request.code else 'None'}...")
    print(f"{Fore.CYAN}[AUTH]   State: {request.state}")
    return handle_google_oauth_callback(request.code, request.state, db,redirect_on_success=False,
        redirect_on_error=False)



@app.get("/api/auth/google/callback")
async def google_oauth_callback_get(
    code: str = Query(None),
    state: str = Query(None),
    db: Session = Depends(get_db)
):

    print(f"{Fore.CYAN}[AUTH] GET /api/auth/google/callback received")
    print(f"{Fore.CYAN}[AUTH]   Code: {code}")
    print(f"{Fore.CYAN}[AUTH]   State: {state}")

    if not code:
        print(f"{Fore.RED}[AUTH] ❌ No authorization code received from Google")
        return {
            "success": False,
            "error": "No authorization code received from Google"
        }

    return handle_google_oauth_callback(code, state or "", db,redirect_on_success=True,
        redirect_on_error=True)



def handle_google_oauth_callback(
    code: str,
    state: str,
    db: Session,
    redirect_on_success: bool,
    redirect_on_error: bool
):
    """
    Handle Google OAuth callback.

    1. User authorizes, Google redirects with code
    2. Backend exchanges code for OAuth token
    3. Backend fetches user info from Google
    4. Backend creates/updates user and session in DB

    Args:
        code: Authorization code from Google
        state: State token for CSRF protection
        db: Database session
        redirect_on_success: Whether to redirect on success (GET flow)
        redirect_on_error: Whether to redirect on error (GET flow)

    Returns:
        JSON response or RedirectResponse with tokens
    """
    print(f"{Fore.CYAN}[AUTH] === GOOGLE OAUTH CALLBACK HANDLER START ===")
    try:
        # Exchange Google auth code for OAuth token (single exchange)
        oauth_token = auth_service.exchange_oauth_code_for_token(
            code,
            state
        )

        if not oauth_token:
            print(f"{Fore.RED}[AUTH] ❌ Token exchange returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=OAUTH_ERROR_EXCHANGE_FAILED
            )

        print(f"{Fore.GREEN}[AUTH] ✅ Token exchange successful")

        # Get user info from Google using the access token
        access_token = oauth_token.get("access_token")
        user_info = auth_service.get_user_info_from_google(access_token)

        if not user_info or not user_info.get("email"):
            print(f"{Fore.RED}[AUTH] ❌ Failed to get user info from Google")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=OAUTH_ERROR_USERINFO_FAILED
            )

        email = user_info["email"]
        name = user_info.get("name", "")
        print(f"{Fore.GREEN}[AUTH] ✅ Got user info: {email}")

        # Create or update user with OAuth token
        user = auth_service.create_or_update_user(
            db=db,
            email=email,
            name=name,
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

        print(f"{Fore.GREEN}[AUTH] ✅ OAuth authentication successful")
        print(f"{Fore.CYAN}[AUTH]   Email: {email}")
        print(f"{Fore.CYAN}[AUTH]   User ID: {user.id}")

        response_payload = {
            OAUTH_REDIRECT_PARAM_ACCESS_TOKEN: session.access_token,
            OAUTH_REDIRECT_PARAM_REFRESH_TOKEN: session.refresh_token,
            OAUTH_REDIRECT_PARAM_TOKEN_TYPE: OAUTH_TOKEN_TYPE_BEARER,
            OAUTH_REDIRECT_PARAM_EXPIRES_IN: config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            OAUTH_REDIRECT_PARAM_USER_ID: user.id,
        }

        if redirect_on_success and config.FRONTEND_OAUTH_REDIRECT_URL:
            redirect_url = build_oauth_redirect_url(
                config.FRONTEND_OAUTH_REDIRECT_URL,
                response_payload
            )
            return RedirectResponse(url=redirect_url)

        return response_payload

    except HTTPException as exc:
        print(f"{Fore.RED}[AUTH] ❌ HTTPException in callback: {exc.detail}")
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
        print(f"{Fore.RED}[AUTH] ❌ Unexpected error in callback: {str(e)}")
        import traceback
        traceback.print_exc()
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


@app.post("/api/auth/logout")
async def logout(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout the current user by invalidating all active sessions.
    """
    try:
        sessions = db.query(database.UserSession).filter(
            database.UserSession.user_id == current_user,
            database.UserSession.is_active == True
        ).all()

        for session in sessions:
            session.is_active = False

        db.commit()

        return {"success": True, "message": "Logged out successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout: {str(e)}"
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


@app.patch("/api/calendar/appointments/{appointment_id}/no-show")
async def mark_calendar_appointment_no_show(
    appointment_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a calendar appointment as no-show.
    """
    try:
        _, credentials, calendar_id = resolve_calendar_credentials(current_user, db)
        update_calendar_event_no_show(
            event_id=appointment_id,
            calendar_id=calendar_id,
            credentials=credentials
        )
        return {
            "success": True,
            "message": NO_SHOW_SUCCESS_MESSAGE,
            "appointment_id": appointment_id,
            "status": APPOINTMENT_STATUS_NO_SHOW
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ERROR_APPOINTMENT_NO_SHOW_FAILED} {str(e)}"
        )


# ============================================================================
# PATIENT ENDPOINTS (/api/patients)
# ============================================================================

@app.get("/api/patients", response_model=List[models.PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all patients belonging to the authenticated doctor.
    """
    try:
        patients = db.query(database.Patient).filter(
            database.Patient.doctor_id == current_user
        ).offset(skip).limit(limit).all()

        results = []
        for patient in patients:
            last_appt = db.query(database.Appointment).filter(
                database.Appointment.patient_id == patient.id
            ).order_by(database.Appointment.date.desc()).first()

            results.append({
                "id": patient.id,
                "name": patient.name,
                "phone": patient.phone,
                "email": patient.email,
                "notes": patient.notes,
                "created_at": patient.created_at,
                "last_appointment": (
                    datetime.strptime(last_appt.date, DATE_INPUT_FORMAT)
                    if last_appt and last_appt.date else None
                ),
            })
        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list patients: {str(e)}"
        )


@app.post("/api/patients", response_model=models.PatientResponse)
async def create_patient(
    request: models.PatientCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new patient record for the authenticated doctor.
    """
    import uuid

    try:
        patient_id = f"pat_{uuid.uuid4().hex[:12]}"
        patient = database.Patient(
            id=patient_id,
            doctor_id=current_user,
            name=request.name,
            phone=request.phone,
            email=request.email,
            notes=request.notes,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        return {
            "id": patient.id,
            "name": patient.name,
            "phone": patient.phone,
            "email": patient.email,
            "notes": patient.notes,
            "created_at": patient.created_at,
            "last_appointment": None,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )


@app.get("/api/patients/{patient_id}", response_model=models.PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get patient details by ID.
    """
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id,
        database.Patient.doctor_id == current_user
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    last_appt = db.query(database.Appointment).filter(
        database.Appointment.patient_id == patient.id
    ).order_by(database.Appointment.date.desc()).first()

    return {
        "id": patient.id,
        "name": patient.name,
        "phone": patient.phone,
        "email": patient.email,
        "notes": patient.notes,
        "created_at": patient.created_at,
        "last_appointment": (
            datetime.strptime(last_appt.date, DATE_INPUT_FORMAT)
            if last_appt and last_appt.date else None
        ),
    }


@app.put("/api/patients/{patient_id}", response_model=models.PatientResponse)
async def update_patient(
    patient_id: str,
    request: models.PatientUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing patient record.
    """
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id,
        database.Patient.doctor_id == current_user
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    try:
        if request.name is not None:
            patient.name = request.name
        if request.phone is not None:
            patient.phone = request.phone
        if request.email is not None:
            patient.email = request.email
        if request.notes is not None:
            patient.notes = request.notes

        patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(patient)

        last_appt = db.query(database.Appointment).filter(
            database.Appointment.patient_id == patient.id
        ).order_by(database.Appointment.date.desc()).first()

        return {
            "id": patient.id,
            "name": patient.name,
            "phone": patient.phone,
            "email": patient.email,
            "notes": patient.notes,
            "created_at": patient.created_at,
            "last_appointment": (
                datetime.strptime(last_appt.date, DATE_INPUT_FORMAT)
                if last_appt and last_appt.date else None
            ),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient: {str(e)}"
        )


@app.delete("/api/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a patient record. Removes the patient from the database.
    """
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id,
        database.Patient.doctor_id == current_user
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    try:
        db.delete(patient)
        db.commit()
        return {"success": True, "message": f"Patient {patient_id} deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete patient: {str(e)}"
        )


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


def find_appointment_by_id_or_calendar_id(db, doctor_id: str, appointment_id: str):
    """Look up an appointment by local ID first, then by calendar_event_id."""
    appointment = db.query(database.Appointment).filter(
        database.Appointment.doctor_id == doctor_id,
        database.Appointment.id == appointment_id
    ).first()

    if not appointment:
        appointment = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == doctor_id,
            database.Appointment.calendar_event_id == appointment_id
        ).first()

    return appointment


@app.put("/api/appointments/{appointment_id}", response_model=models.AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    request: models.AppointmentUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing appointment's details in the database.
    """
    appointment = find_appointment_by_id_or_calendar_id(db, current_user, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    try:
        if request.date is not None:
            appointment.date = request.date
        if request.time is not None:
            appointment.time = request.time
        if request.type is not None:
            appointment.type = request.type
        if request.notes is not None:
            appointment.notes = request.notes
        if request.status is not None:
            appointment.status = request.status

        appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(appointment)

        patient_name = appointment.patient.name if appointment.patient else APPOINTMENT_SUMMARY_FALLBACK

        return {
            "id": appointment.id,
            "calendar_event_id": appointment.calendar_event_id,
            "patient_id": appointment.patient_id,
            "patient_name": patient_name,
            "date": appointment.date,
            "time": appointment.time,
            "duration_minutes": appointment.duration_minutes or config.APPOINTMENT_DURATION_MINUTES,
            "type": appointment.type,
            "status": appointment.status,
            "notes": appointment.notes,
            "reminder_sent": appointment.reminder_sent or False,
            "created_at": appointment.created_at,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment: {str(e)}"
        )


@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment by setting its status to cancelled.
    """
    appointment = find_appointment_by_id_or_calendar_id(db, current_user, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    try:
        appointment.status = APPOINTMENT_STATUS_CANCELLED
        appointment.updated_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": f"Appointment {appointment_id} cancelled"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel appointment: {str(e)}"
        )


@app.post("/api/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str,
    request: models.AppointmentConfirm,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm an appointment by setting its status to confirmed.
    """
    appointment = find_appointment_by_id_or_calendar_id(db, current_user, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_APPOINTMENT_NOT_FOUND
        )

    try:
        appointment.status = "confirmed"
        appointment.updated_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "Appointment confirmed"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm appointment: {str(e)}"
        )


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
        _, credentials, calendar_id = resolve_calendar_credentials(current_user, db)

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
        update_calendar_event_no_show(
            event_id=calendar_event_id,
            calendar_id=calendar_id,
            credentials=credentials
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
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all calls (inbound and outbound) for the authenticated doctor.
    """
    try:
        calls = db.query(database.Call).filter(
            database.Call.doctor_id == current_user
        ).order_by(
            database.Call.created_at.desc()
        ).offset(skip).limit(limit).all()

        return [
            {
                "id": call.id,
                "call_sid": call.call_sid or "",
                "patient_id": call.patient_id or "",
                "patient_name": call.patient.name if call.patient else "",
                "phone": call.phone_number,
                "type": call.type or "",
                "status": call.status or "",
                "duration_seconds": call.duration_seconds or 0,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "created_at": call.created_at,
            }
            for call in calls
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list calls: {str(e)}"
        )


@app.get("/api/calls/scheduled", response_model=models.ScheduledCallsResponse)
async def get_scheduled_calls(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get scheduled outbound calls for the authenticated doctor.
    """
    try:
        calls = db.query(database.Call).filter(
            database.Call.doctor_id == current_user,
            database.Call.status.in_(["initiated", "scheduled", "ringing"])
        ).order_by(database.Call.created_at.desc()).all()

        call_list = [
            {
                "id": call.id,
                "call_sid": call.call_sid or "",
                "patient_id": call.patient_id or "",
                "patient_name": call.patient.name if call.patient else "",
                "phone": call.phone_number,
                "type": call.type or "",
                "status": call.status or "",
                "duration_seconds": call.duration_seconds or 0,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "created_at": call.created_at,
            }
            for call in calls
        ]
        return {"count": len(call_list), "calls": call_list}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduled calls: {str(e)}"
        )


@app.get("/api/calls/{call_id}", response_model=models.CallResponse)
async def get_call(
    call_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get call details by ID.
    """
    call = db.query(database.Call).filter(
        database.Call.id == call_id,
        database.Call.doctor_id == current_user
    ).first()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    return {
        "id": call.id,
        "call_sid": call.call_sid or "",
        "patient_id": call.patient_id or "",
        "patient_name": call.patient.name if call.patient else "",
        "phone": call.phone_number,
        "type": call.type or "",
        "status": call.status or "",
        "duration_seconds": call.duration_seconds or 0,
        "started_at": call.started_at,
        "ended_at": call.ended_at,
        "created_at": call.created_at,
    }


@app.post("/api/calls/manual", response_model=models.CallResponse)
async def make_manual_call(
    request: models.CallCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate an outbound call to a patient.

    Looks up the patient by ID, initiates a Twilio call to their
    phone number, and stores the call record in the database.
    """
    import uuid

    # Look up patient to get their phone number
    patient = db.query(database.Patient).filter(
        database.Patient.id == request.patient_id,
        database.Patient.doctor_id == current_user
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    call_id = f"call_{uuid.uuid4().hex[:12]}"
    call_type = request.call_type or "manual"
    now = datetime.utcnow()

    try:
        # Build inline TwiML so Twilio doesn't need a public webhook URL
        twiml_message = (
            f"<Response><Say voice=\"alice\">{request.message}</Say></Response>"
        )

        # Initiate Twilio call with real patient phone
        twilio_result = twilio.make_outbound_call(
            to_number=patient.phone,
            twiml_body=twiml_message,
        )

        # Save call record to database
        call_record = database.Call(
            id=call_id,
            doctor_id=current_user,
            patient_id=patient.id,
            call_sid=twilio_result["call_sid"],
            direction="outbound",
            type=call_type,
            phone_number=patient.phone,
            status=twilio_result.get("status", "initiated"),
            duration_seconds=0,
            started_at=now,
            created_at=now,
        )
        db.add(call_record)
        db.commit()

        return {
            "id": call_id,
            "call_sid": twilio_result["call_sid"],
            "patient_id": patient.id,
            "patient_name": patient.name,
            "phone": patient.phone,
            "type": call_type,
            "status": twilio_result.get("status", "initiated"),
            "duration_seconds": 0,
            "started_at": now,
            "ended_at": None,
            "created_at": now,
        }

    except TwilioCallError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=config.ERROR_CALL_FAILED
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule call: {str(e)}"
        )


# ============================================================================
# DASHBOARD ENDPOINTS (/api/dashboard)
# ============================================================================

@app.get("/api/dashboard/stats", response_model=models.DashboardStats)
async def get_dashboard_stats(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics calculated from the database.

    Counts patients, appointments (by status), and calls
    belonging to the authenticated doctor.
    """
    from sqlalchemy import func

    try:
        total_patients = db.query(func.count(database.Patient.id)).filter(
            database.Patient.doctor_id == current_user
        ).scalar() or 0

        total_appointments = db.query(func.count(database.Appointment.id)).filter(
            database.Appointment.doctor_id == current_user
        ).scalar() or 0

        now_date = datetime.utcnow().strftime(DATE_OUTPUT_FORMAT)

        upcoming_appointments = db.query(func.count(database.Appointment.id)).filter(
            database.Appointment.doctor_id == current_user,
            database.Appointment.date >= now_date,
            database.Appointment.status.in_([
                APPOINTMENT_STATUS_SCHEDULED, "confirmed"
            ])
        ).scalar() or 0

        completed_appointments = db.query(func.count(database.Appointment.id)).filter(
            database.Appointment.doctor_id == current_user,
            database.Appointment.status == "completed"
        ).scalar() or 0

        no_show_count = db.query(func.count(database.Appointment.id)).filter(
            database.Appointment.doctor_id == current_user,
            database.Appointment.status == APPOINTMENT_STATUS_NO_SHOW
        ).scalar() or 0

        total_calls_made = db.query(func.count(database.Call.id)).filter(
            database.Call.doctor_id == current_user
        ).scalar() or 0

        successful_calls = db.query(func.count(database.Call.id)).filter(
            database.Call.doctor_id == current_user,
            database.Call.status == "completed"
        ).scalar() or 0

        return {
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "upcoming_appointments": upcoming_appointments,
            "completed_appointments": completed_appointments,
            "no_show_count": no_show_count,
            "total_calls_made": total_calls_made,
            "successful_calls": successful_calls,
        }

    except Exception as e:
        print(f"{Fore.RED}[DASHBOARD] ❌ Failed to load stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard stats: {str(e)}"
        )


@app.get("/api/dashboard/activity", response_model=models.DashboardActivity)
async def get_dashboard_activity(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent activity: latest appointments, calls, and upcoming events.

    Queries the database for the most recent records belonging to the
    authenticated doctor.
    """
    RECENT_ACTIVITY_LIMIT = 5

    try:
        recent_appointments = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == current_user
        ).order_by(
            database.Appointment.updated_at.desc()
        ).limit(RECENT_ACTIVITY_LIMIT).all()

        recent_calls = db.query(database.Call).filter(
            database.Call.doctor_id == current_user
        ).order_by(
            database.Call.created_at.desc()
        ).limit(RECENT_ACTIVITY_LIMIT).all()

        now_date = datetime.utcnow().strftime(DATE_OUTPUT_FORMAT)
        upcoming_events = db.query(database.Appointment).filter(
            database.Appointment.doctor_id == current_user,
            database.Appointment.date >= now_date,
            database.Appointment.status.in_([
                APPOINTMENT_STATUS_SCHEDULED, "confirmed"
            ])
        ).order_by(
            database.Appointment.date.asc(),
            database.Appointment.time.asc()
        ).limit(RECENT_ACTIVITY_LIMIT).all()

        def appointment_to_dict(appt):
            patient_name = APPOINTMENT_SUMMARY_FALLBACK
            if appt.patient:
                patient_name = appt.patient.name
            return {
                "id": appt.id,
                "calendar_event_id": appt.calendar_event_id,
                "patient_id": appt.patient_id,
                "patient_name": patient_name,
                "date": appt.date,
                "time": appt.time,
                "duration_minutes": appt.duration_minutes or config.APPOINTMENT_DURATION_MINUTES,
                "type": appt.type or APPOINTMENT_TYPE_FALLBACK,
                "status": appt.status or APPOINTMENT_STATUS_SCHEDULED,
                "notes": appt.notes,
                "reminder_sent": appt.reminder_sent or False,
                "created_at": appt.created_at,
            }

        def call_to_dict(call):
            patient_name = ""
            if call.patient:
                patient_name = call.patient.name
            return {
                "id": call.id,
                "call_sid": call.call_sid or "",
                "patient_id": call.patient_id or "",
                "patient_name": patient_name,
                "phone": call.phone_number,
                "type": call.type or "",
                "status": call.status or "",
                "duration_seconds": call.duration_seconds or 0,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "created_at": call.created_at,
            }

        return {
            "recent_appointments": [appointment_to_dict(a) for a in recent_appointments],
            "recent_calls": [call_to_dict(c) for c in recent_calls],
            "upcoming_events": [appointment_to_dict(a) for a in upcoming_events],
        }

    except Exception as e:
        print(f"{Fore.RED}[DASHBOARD] ❌ Failed to load activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard activity: {str(e)}"
        )


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
        # Use CalendarService to check availability
        date_str, formatted_date, slots, message = cal_service.check_availability(date)

        # Convert TimeSlot objects to dicts for JSON response
        available_slots = [
            {
                "time": slot.formatted_time,
                "date": slot.formatted_date,
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat()
            }
            for slot in slots
        ]

        print(f"{Fore.GREEN}[AGENT API] ✅ check_availability returned: {len(available_slots)} slots")
        return {
            "success": True,
            "date": date_str,
            "formatted_date": formatted_date,
            "available_slots": available_slots,
            "message": message
        }

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
            db.commit()
            print(f"{Fore.GREEN}[AGENT API] ✅ Created patient: {patient_id}")
        else:
            print(f"{Fore.GREEN}[AGENT API] ✅ Found existing patient: {patient.id}")

        # Parse datetime from date and time strings
        from datetime import datetime as dt_parse
        appointment_datetime = dt_parse.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        # Map appointment_type string to AppointmentType enum
        from src.api.schemas.calendar import AppointmentType
        appt_type_map = {
            "General Checkup": AppointmentType.CHECKUP,
            "Follow-up": AppointmentType.FOLLOW_UP,
            "Consultation": AppointmentType.CONSULTATION,
        }
        appt_type = appt_type_map.get(appointment_type, AppointmentType.CHECKUP)

        # Book appointment using CalendarService
        success, message, confirmation_id, appointment = cal_service.create_appointment(
            patient_name=patient_name,
            patient_phone=phone_number,
            appointment_datetime=appointment_datetime,
            appointment_type=appt_type
        )

        if not success:
            print(f"{Fore.RED}[AGENT API] ❌ booking failed: {message}")
            return {
                "success": False,
                "error": message
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Appointment created: {confirmation_id}")
        return {
            "success": True,
            "appointment_id": confirmation_id,
            "confirmation_number": confirmation_id,
            "message": message,
            "patient_name": patient_name,
            "date": date,
            "time": time
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
        # Verify patient owns this appointment (check in Google Calendar via service)
        patient = db.query(database.Patient).filter(
            database.Patient.phone == phone_number
        ).first()

        if not patient:
            print(f"{Fore.RED}[AGENT API] ❌ Patient not found")
            return {
                "success": False,
                "error": "Patient not found"
            }

        # Parse new datetime
        from datetime import datetime as dt_parse
        new_appointment_datetime = dt_parse.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")

        # Reschedule using CalendarService
        success, message, appointment = cal_service.reschedule_appointment(
            appointment_id=appointment_id,
            new_datetime=new_appointment_datetime
        )

        if not success:
            print(f"{Fore.RED}[AGENT API] ❌ Reschedule failed: {message}")
            return {
                "success": False,
                "error": message
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Rescheduled appointment {appointment_id} to {new_date} {new_time}")

        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": f"Your appointment has been rescheduled to {new_date} at {new_time}"
        }

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
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

        # Cancel appointment using CalendarService
        success, message = cal_service.cancel_appointment(appointment_id=appointment_id)

        if not success:
            print(f"{Fore.RED}[AGENT API] ❌ Cancellation failed: {message}")
            return {
                "success": False,
                "error": message
            }

        print(f"{Fore.GREEN}[AGENT API] ✅ Appointment cancelled")

        return {
            "success": True,
            "message": f"Your appointment has been cancelled. {message}"
        }

    except Exception as e:
        print(f"{Fore.RED}[AGENT API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
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
