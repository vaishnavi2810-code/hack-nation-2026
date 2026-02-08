"""
CallPilot Configuration

All configurable values are loaded from environment variables.
Copy .env.example to .env and fill in your values.
"""

import os
from datetime import time
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class CalendarConfig(BaseSettings):
    """Google Calendar configuration."""
    
    # Google Calendar API
    google_credentials_path: str = Field(
        default="credentials.json",
        description="Path to Google OAuth credentials JSON file"
    )
    google_token_path: str = Field(
        default="token.json",
        description="Path to store OAuth token"
    )
    calendar_id: str = Field(
        default="primary",
        description="Google Calendar ID (use 'primary' for main calendar)"
    )
    
    # Appointment Settings
    appointment_duration_minutes: int = Field(
        default=30,
        description="Default appointment duration in minutes"
    )
    buffer_between_appointments_minutes: int = Field(
        default=0,
        description="Buffer time between appointments"
    )
    
    # Doctor Availability
    available_start_hour: int = Field(
        default=9,
        description="Start of available hours (24h format)"
    )
    available_start_minute: int = Field(
        default=0,
        description="Start minute"
    )
    available_end_hour: int = Field(
        default=17,
        description="End of available hours (24h format)"
    )
    available_end_minute: int = Field(
        default=0,
        description="End minute"
    )
    
    # Available days (0=Monday, 6=Sunday)
    available_days: List[int] = Field(
        default=[0, 1, 2, 3, 4, 5, 6],
        description="Days of week available (0=Mon, 6=Sun)"
    )
    
    # Timezone
    timezone: str = Field(
        default="America/New_York",
        description="Timezone for appointments"
    )
    
    @property
    def available_start_time(self) -> time:
        return time(self.available_start_hour, self.available_start_minute)
    
    @property
    def available_end_time(self) -> time:
        return time(self.available_end_hour, self.available_end_minute)
    
    class Config:
        env_prefix = "CALLPILOT_"
        env_file = ".env"


class TwilioConfig(BaseSettings):
    """Twilio configuration for voice calls."""
    
    account_sid: str = Field(default="", description="Twilio Account SID")
    auth_token: str = Field(default="", description="Twilio Auth Token")
    phone_number: str = Field(default="", description="Twilio phone number for inbound/outbound calls")
    
    class Config:
        env_prefix = "TWILIO_"
        env_file = ".env"


class ElevenLabsConfig(BaseSettings):
    """ElevenLabs configuration for AI voice agent."""
    
    api_key: str = Field(default="", description="ElevenLabs API key")
    agent_id: str = Field(default="", description="ElevenLabs agent ID")
    voice_id: str = Field(default="", description="Voice ID for the agent")
    
    class Config:
        env_prefix = "ELEVENLABS_"
        env_file = ".env"


class ReminderConfig(BaseSettings):
    """Reminder settings."""
    
    hours_before_appointment: int = Field(
        default=3,
        description="Hours before appointment to send reminder"
    )
    cron_interval_minutes: int = Field(
        default=15,
        description="How often to check for upcoming appointments"
    )
    
    class Config:
        env_prefix = "REMINDER_"
        env_file = ".env"


# Global config instances
calendar_config = CalendarConfig()
twilio_config = TwilioConfig()
elevenlabs_config = ElevenLabsConfig()
reminder_config = ReminderConfig()