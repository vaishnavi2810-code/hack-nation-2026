"""
Google Calendar API client setup and authentication.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from src.config import calendar_config

# Required scopes for calendar access
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]


class CalendarClient:
    """Singleton client for Google Calendar API."""
    
    _instance = None
    _service: Resource = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._service is None:
            self._service = self._authenticate()
    
    def _authenticate(self) -> Resource:
        """Authenticate with Google Calendar API."""
        creds = None
        token_path = calendar_config.google_token_path
        credentials_path = calendar_config.google_credentials_path
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {credentials_path}\n"
                        "Download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future use
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        
        return build("calendar", "v3", credentials=creds)
    
    @property
    def service(self) -> Resource:
        """Get the Calendar API service."""
        return self._service
    
    @property
    def calendar_id(self) -> str:
        """Get configured calendar ID."""
        return calendar_config.calendar_id


def get_calendar_client() -> CalendarClient:
    """Get or create the calendar client instance."""
    return CalendarClient()


def get_calendar_service() -> Resource:
    """Convenience function to get just the service."""
    return get_calendar_client().service