"""
Configuration loader for CallPilot application.

Loads and validates all environment variables from .env file.
NO HARDCODED VALUES - All config comes from environment or constants.
"""

import os
import sys
from dotenv import load_dotenv
from colorama import Fore, init

init(autoreset=True)

# Load .env file
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid"""
    pass


def validate_required_var(var_name: str, description: str = "") -> str:
    """Validate that a required environment variable is set"""
    value = os.getenv(var_name)
    if not value:
        error_msg = f"Missing required environment variable: {var_name}"
        if description:
            error_msg += f" ({description})"
        print(f"{Fore.RED}❌ {error_msg}")
        raise ConfigError(error_msg)
    return value


def get_optional_var(var_name: str, default: str = None) -> str:
    """Get an optional environment variable with default"""
    return os.getenv(var_name, default)


# ============================================================================
# ELEVENLABS CONFIG
# ============================================================================
ELEVENLABS_API_KEY = validate_required_var(
    "ELEVENLABS_API_KEY",
    "ElevenLabs API key from https://elevenlabs.io/app/settings/api-keys"
)
ELEVENLABS_AGENT_ID = validate_required_var(
    "ELEVENLABS_AGENT_ID",
    "ElevenLabs Agent ID from dashboard"
)
ELEVENLABS_API_BASE_URL = get_optional_var(
    "ELEVENLABS_API_BASE_URL",
    "https://api.elevenlabs.io/v1"
)

# ============================================================================
# TWILIO CONFIG
# ============================================================================
TWILIO_ACCOUNT_SID = validate_required_var(
    "TWILIO_ACCOUNT_SID",
    "Twilio Account SID from console.twilio.com"
)
TWILIO_AUTH_TOKEN = validate_required_var(
    "TWILIO_AUTH_TOKEN",
    "Twilio Auth Token from console.twilio.com"
)
TWILIO_PHONE_NUMBER = validate_required_var(
    "TWILIO_PHONE_NUMBER",
    "Your Twilio phone number (E.164 format, e.g., +12125551234)"
)
TWILIO_API_BASE_URL = get_optional_var(
    "TWILIO_API_BASE_URL",
    "https://api.twilio.com"
)

# ============================================================================
# GOOGLE CALENDAR CONFIG
# ============================================================================
GOOGLE_CALENDAR_ID = validate_required_var(
    "GOOGLE_CALENDAR_ID",
    "Doctor's Google Calendar ID"
)
GOOGLE_CREDENTIALS_PATH = validate_required_var(
    "GOOGLE_CREDENTIALS_PATH",
    "Path to Google service account JSON file"
)
GOOGLE_OAUTH_CLIENT_ID = validate_required_var(
    "GOOGLE_OAUTH_CLIENT_ID",
    "Google OAuth client ID from Google Cloud Console"
)
GOOGLE_OAUTH_CLIENT_SECRET = validate_required_var(
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "Google OAuth client secret from Google Cloud Console"
)
DEFAULT_GOOGLE_OAUTH_SCOPES = (
    "https://www.googleapis.com/auth/calendar,"
    "openid,"
    "https://www.googleapis.com/auth/userinfo.email,"
    "https://www.googleapis.com/auth/userinfo.profile"
)
GOOGLE_OAUTH_SCOPES = [
    scope.strip()
    for scope in get_optional_var(
        "GOOGLE_OAUTH_SCOPES",
        DEFAULT_GOOGLE_OAUTH_SCOPES
    ).split(",")
    if scope.strip()
]

# ============================================================================
# DOCTOR SETTINGS
# ============================================================================
DOCTOR_TIMEZONE = get_optional_var("DOCTOR_TIMEZONE", "America/New_York")
DOCTOR_EMAIL = validate_required_var(
    "DOCTOR_EMAIL",
    "Doctor's email address"
)
APPOINTMENT_DURATION_MINUTES = int(
    get_optional_var("APPOINTMENT_DURATION_MINUTES", "30")
)
APPOINTMENT_BUFFER_MINUTES = int(
    get_optional_var("APPOINTMENT_BUFFER_MINUTES", "10")
)

# ============================================================================
# REMINDER SCHEDULER
# ============================================================================
REMINDER_HOURS_BEFORE = int(
    get_optional_var("REMINDER_HOURS_BEFORE", "3")
)
REMINDER_CHECK_INTERVAL_SECONDS = int(
    get_optional_var("REMINDER_CHECK_INTERVAL_SECONDS", "900")
)
ENABLE_REMINDERS = get_optional_var("ENABLE_REMINDERS", "true").lower() == "true"

# ============================================================================
# DATABASE CONFIG
# ============================================================================
DATABASE_URL = get_optional_var(
    "DATABASE_URL",
    "sqlite:///./callpilot.db"
)

# ============================================================================
# AUTHENTICATION & SECURITY
# ============================================================================
SECRET_KEY = validate_required_var(
    "SECRET_KEY",
    "Secret key for JWT token signing (generate a random string)"
)
ALGORITHM = get_optional_var("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    get_optional_var("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS = int(
    get_optional_var("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

# ============================================================================
# APPLICATION CONFIG
# ============================================================================
APP_NAME = get_optional_var("APP_NAME", "CallPilot")
APP_VERSION = get_optional_var("APP_VERSION", "0.1.0")
DEBUG = get_optional_var("DEBUG", "false").lower() == "true"
LOG_LEVEL = get_optional_var("LOG_LEVEL", "INFO")
API_BASE_URL = get_optional_var("API_BASE_URL", "http://localhost:8000")
FRONTEND_OAUTH_REDIRECT_URL = get_optional_var("FRONTEND_OAUTH_REDIRECT_URL", "")

# ============================================================================
# CORS CONFIG
# ============================================================================
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in get_optional_var("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# ============================================================================
# WEBHOOK CONFIG
# ============================================================================
WEBHOOK_URL = validate_required_var(
    "WEBHOOK_URL",
    "Webhook URL for ElevenLabs callbacks (e.g., http://localhost:8000/api/webhooks/elevenlabs)"
)

# ============================================================================
# SMS SETTINGS
# ============================================================================
ENABLE_SMS_CONFIRMATIONS = get_optional_var(
    "ENABLE_SMS_CONFIRMATIONS",
    "true"
).lower() == "true"
SMS_CONFIRMATION_MESSAGE = get_optional_var(
    "SMS_CONFIRMATION_MESSAGE",
    "Hi {name}, your appointment is confirmed for {date} at {time}. Reply STOP to opt out."
)

# ============================================================================
# FEATURE FLAGS
# ============================================================================
ENABLE_PATIENT_MANAGEMENT = get_optional_var(
    "ENABLE_PATIENT_MANAGEMENT",
    "true"
).lower() == "true"
ENABLE_APPOINTMENT_REMINDERS = get_optional_var(
    "ENABLE_APPOINTMENT_REMINDERS",
    "true"
).lower() == "true"
ENABLE_OUTBOUND_CALLS = get_optional_var(
    "ENABLE_OUTBOUND_CALLS",
    "true"
).lower() == "true"
ENABLE_CALL_LOGGING = get_optional_var(
    "ENABLE_CALL_LOGGING",
    "true"
).lower() == "true"

# ============================================================================
# API TIMEOUTS AND LIMITS
# ============================================================================
TWILIO_API_TIMEOUT_SECONDS = int(
    get_optional_var("TWILIO_API_TIMEOUT_SECONDS", "10")
)
ELEVENLABS_API_TIMEOUT_SECONDS = int(
    get_optional_var("ELEVENLABS_API_TIMEOUT_SECONDS", "10")
)
GOOGLE_API_TIMEOUT_SECONDS = int(
    get_optional_var("GOOGLE_API_TIMEOUT_SECONDS", "10")
)

# ============================================================================
# MESSAGES (Stored as constants to avoid magic strings)
# ============================================================================
MSG_APPOINTMENT_CONFIRMED = "Your appointment has been confirmed."
MSG_APPOINTMENT_CANCELLED = "Your appointment has been cancelled."
MSG_APPOINTMENT_RESCHEDULED = "Your appointment has been rescheduled."
MSG_APPOINTMENT_REMINDER = "Hi {name}, reminder about your {time} appointment today."
ERROR_INVALID_CREDENTIALS = "Invalid email or password."
ERROR_APPOINTMENT_NOT_FOUND = "Appointment not found."
ERROR_CALENDAR_DISCONNECT = "Calendar has been disconnected."
ERROR_CALL_FAILED = "Failed to initiate call. Please try again."


def validate_config() -> bool:
    """
    Validate that all required config is properly set.
    Call this on application startup.
    """
    try:
        # All required vars are validated on import above
        print(f"{Fore.GREEN}✅ Configuration validated successfully")
        return True
    except ConfigError as e:
        print(f"{Fore.RED}❌ Configuration error: {e}")
        sys.exit(1)
