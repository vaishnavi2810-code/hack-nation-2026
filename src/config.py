"""
Configuration loader for CallPilot application.

Loads and validates all environment variables from .env file.
Combines Pydantic settings with direct environment variable loading.
"""

import os
import sys
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

try:
    from colorama import Fore, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class Fore:
        RED = ""
        GREEN = ""

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
# PYDANTIC CONFIG CLASSES (for Google Calendar)
# ============================================================================

class GoogleCalendarConfig(BaseSettings):
    """Google Calendar API configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_",
        env_file=".env",
        extra="ignore"
    )
    
    client_id: str = Field(default="", description="Google OAuth Client ID")
    client_secret: str = Field(default="", description="Google OAuth Client Secret")
    redirect_uri: str = Field(
        default="http://localhost:8000/api/calendar/auth-callback",
        description="OAuth redirect URI"
    )
    scopes: List[str] = Field(
        default=[
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ],
        description="Google Calendar API scopes"
    )
    token_file: str = Field(
        default="token.json",
        description="Path to store OAuth tokens"
    )


class AppointmentConfig(BaseSettings):
    """Appointment settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="APPOINTMENT_",
        env_file=".env",
        extra="ignore"
    )
    
    duration_minutes: int = Field(default=30, description="Default appointment duration")
    buffer_minutes: int = Field(default=0, description="Buffer between appointments")
    
    available_start_hour: int = Field(default=9, description="Start hour")
    available_start_minute: int = Field(default=0, description="Start minute")
    available_end_hour: int = Field(default=17, description="End hour")
    available_end_minute: int = Field(default=0, description="End minute")
    
    available_days: List[int] = Field(
        default=[0, 1, 2, 3, 4, 5, 6],
        description="Days of week (0=Mon, 6=Sun)"
    )
    
    timezone: str = Field(default="America/New_York", description="Timezone")


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore"
    )
    
    app_name: str = Field(default="CallPilot", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")


# Global Pydantic config instances
google_config = GoogleCalendarConfig()
appointment_config = AppointmentConfig()
app_config = AppConfig()

# ============================================================================
# APPOINTMENT CONFIG (top-level constants from Pydantic model)
# ============================================================================
APPOINTMENT_DURATION_MINUTES = int(
    get_optional_var("APPOINTMENT_DURATION_MINUTES", str(appointment_config.duration_minutes))
)
APPOINTMENT_BUFFER_MINUTES = int(
    get_optional_var("APPOINTMENT_BUFFER_MINUTES", str(appointment_config.buffer_minutes))
)

# ============================================================================
# GOOGLE OAUTH CONFIG
# ============================================================================
DEFAULT_GOOGLE_CREDENTIALS_PATH = "./google_credentials.json"
GOOGLE_CREDENTIALS_PATH = get_optional_var(
    "GOOGLE_CREDENTIALS_PATH",
    DEFAULT_GOOGLE_CREDENTIALS_PATH
)
DEFAULT_GOOGLE_CALENDAR_ID = "primary"
GOOGLE_CALENDAR_ID = get_optional_var(
    "GOOGLE_CALENDAR_ID",
    DEFAULT_GOOGLE_CALENDAR_ID
)
DEFAULT_GOOGLE_OAUTH_SCOPES = (
    "https://www.googleapis.com/auth/calendar,"
    "openid,"
    "https://www.googleapis.com/auth/userinfo.email,"
    "https://www.googleapis.com/auth/userinfo.profile"
)
GOOGLE_OAUTH_SCOPES_SEPARATOR = ","
GOOGLE_OAUTH_SCOPES_RAW = get_optional_var(
    "GOOGLE_OAUTH_SCOPES",
    DEFAULT_GOOGLE_OAUTH_SCOPES
)
GOOGLE_OAUTH_SCOPES = [
    scope.strip()
    for scope in GOOGLE_OAUTH_SCOPES_RAW.split(GOOGLE_OAUTH_SCOPES_SEPARATOR)
    if scope.strip()
]

GOOGLE_REDIRECT_URI = get_optional_var(
    "GOOGLE_REDIRECT_URI",
    None
)

DEFAULT_CALENDAR_MAX_RESULTS = "250"
CALENDAR_MAX_RESULTS = int(get_optional_var("CALENDAR_MAX_RESULTS", DEFAULT_CALENDAR_MAX_RESULTS))
DEFAULT_APPOINTMENTS_LOOKAHEAD_DAYS = "1"
APPOINTMENTS_LOOKAHEAD_DAYS = int(
    get_optional_var("APPOINTMENTS_LOOKAHEAD_DAYS", DEFAULT_APPOINTMENTS_LOOKAHEAD_DAYS)
)


# ============================================================================
# ELEVENLABS CONFIG
# ============================================================================
ELEVENLABS_API_KEY = get_optional_var("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = get_optional_var("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_API_BASE_URL = get_optional_var(
    "ELEVENLABS_API_BASE_URL",
    "https://api.elevenlabs.io/v1"
)

# ============================================================================
# TWILIO CONFIG
# ============================================================================
TWILIO_ACCOUNT_SID = get_optional_var("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = get_optional_var("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = get_optional_var("TWILIO_PHONE_NUMBER", "")
TWILIO_API_BASE_URL = get_optional_var(
    "TWILIO_API_BASE_URL",
    "https://api.twilio.com"
)

# ============================================================================
# DOCTOR SETTINGS
# ============================================================================
DOCTOR_TIMEZONE = get_optional_var("DOCTOR_TIMEZONE", "America/New_York")
DOCTOR_EMAIL = get_optional_var("DOCTOR_EMAIL", "")

# ============================================================================
# REMINDER SCHEDULER
# ============================================================================
REMINDER_HOURS_BEFORE = int(get_optional_var("REMINDER_HOURS_BEFORE", "3"))
REMINDER_CHECK_INTERVAL_SECONDS = int(get_optional_var("REMINDER_CHECK_INTERVAL_SECONDS", "900"))
ENABLE_REMINDERS = get_optional_var("ENABLE_REMINDERS", "true").lower() == "true"

# ============================================================================
# DATABASE CONFIG
# ============================================================================
DATABASE_URL = get_optional_var("DATABASE_URL", "sqlite:///./callpilot.db")

# ============================================================================
# AUTHENTICATION & SECURITY
# ============================================================================
SECRET_KEY = get_optional_var("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = get_optional_var("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_optional_var("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(get_optional_var("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ============================================================================
# APPLICATION CONFIG
# ============================================================================
APP_NAME = get_optional_var("APP_NAME", "CallPilot")
APP_VERSION = get_optional_var("APP_VERSION", "0.1.0")
DEBUG = get_optional_var("DEBUG", "false").lower() == "true"
LOG_LEVEL = get_optional_var("LOG_LEVEL", "INFO")
API_BASE_URL = get_optional_var("API_BASE_URL", "http://localhost:8000")
DEFAULT_CORS_ALLOWED_ORIGINS = "http://localhost:5173"
CORS_ALLOWED_ORIGINS_SEPARATOR = ","
CORS_ALLOWED_ORIGINS_RAW = get_optional_var("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ALLOWED_ORIGINS)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in CORS_ALLOWED_ORIGINS_RAW.split(CORS_ALLOWED_ORIGINS_SEPARATOR)
    if origin.strip()
]
DEFAULT_FRONTEND_OAUTH_REDIRECT_URL = "http://localhost:5173/oauth/callback"
FRONTEND_OAUTH_REDIRECT_URL = get_optional_var(
    "FRONTEND_OAUTH_REDIRECT_URL",
    DEFAULT_FRONTEND_OAUTH_REDIRECT_URL
)

# ============================================================================
# WEBHOOK CONFIG
# ============================================================================
WEBHOOK_URL = get_optional_var("WEBHOOK_URL", "http://localhost:8000/api/webhooks/elevenlabs")

# ============================================================================
# SMS SETTINGS
# ============================================================================
ENABLE_SMS_CONFIRMATIONS = get_optional_var("ENABLE_SMS_CONFIRMATIONS", "true").lower() == "true"
SMS_CONFIRMATION_MESSAGE = get_optional_var(
    "SMS_CONFIRMATION_MESSAGE",
    "Hi {name}, your appointment is confirmed for {date} at {time}. Reply STOP to opt out."
)

# ============================================================================
# FEATURE FLAGS
# ============================================================================
ENABLE_PATIENT_MANAGEMENT = get_optional_var("ENABLE_PATIENT_MANAGEMENT", "true").lower() == "true"
ENABLE_APPOINTMENT_REMINDERS = get_optional_var("ENABLE_APPOINTMENT_REMINDERS", "true").lower() == "true"
ENABLE_OUTBOUND_CALLS = get_optional_var("ENABLE_OUTBOUND_CALLS", "true").lower() == "true"
ENABLE_CALL_LOGGING = get_optional_var("ENABLE_CALL_LOGGING", "true").lower() == "true"

# ============================================================================
# API TIMEOUTS AND LIMITS
# ============================================================================
TWILIO_API_TIMEOUT_SECONDS = int(get_optional_var("TWILIO_API_TIMEOUT_SECONDS", "10"))
ELEVENLABS_API_TIMEOUT_SECONDS = int(get_optional_var("ELEVENLABS_API_TIMEOUT_SECONDS", "10"))
GOOGLE_API_TIMEOUT_SECONDS = int(get_optional_var("GOOGLE_API_TIMEOUT_SECONDS", "10"))

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
    print(f"{Fore.GREEN}✅ Configuration loaded successfully")
    return True