"""
CallPilot Configuration

All settings loaded from environment variables.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class GoogleCalendarConfig(BaseSettings):
    """Google Calendar API configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_",
        env_file=".env",
        extra="ignore"  # Ignore extra fields
    )
    
    client_id: str = Field(default="", description="Google OAuth Client ID")
    client_secret: str = Field(default="", description="Google OAuth Client Secret")
    redirect_uri: str = Field(
        default="http://localhost:8000/api/auth/google/callback",
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
        extra="ignore"  # Ignore extra fields
    )
    
    duration_minutes: int = Field(default=30, description="Default appointment duration")
    buffer_minutes: int = Field(default=0, description="Buffer between appointments")
    
    # Doctor availability (24h format)
    available_start_hour: int = Field(default=9, description="Start hour")
    available_start_minute: int = Field(default=0, description="Start minute")
    available_end_hour: int = Field(default=17, description="End hour")
    available_end_minute: int = Field(default=0, description="End minute")
    
    # Available days (0=Monday, 6=Sunday)
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
        extra="ignore"  # Ignore extra fields
    )
    
    app_name: str = Field(default="CallPilot", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")


# Global config instances
google_config = GoogleCalendarConfig()
appointment_config = AppointmentConfig()
app_config = AppConfig()