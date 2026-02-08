"""
Google OAuth authentication handling.
"""

import os
import json
from typing import Optional, Tuple
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.config import google_config


class GoogleAuthManager:
    """Manages Google OAuth authentication."""
    
    def __init__(self):
        self.client_id = google_config.client_id
        self.client_secret = google_config.client_secret
        self.redirect_uri = google_config.redirect_uri
        self.scopes = google_config.scopes
        self.token_file = google_config.token_file
    
    def get_auth_url(self) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Returns:
            Authorization URL to redirect user to
        """
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        
        return auth_url
    
    def handle_callback(self, code: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Tuple of (success, message, email)
        """
        try:
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save tokens
            self._save_tokens(credentials)
            
            # Get user email
            email = self._get_user_email(credentials)
            
            return True, "Successfully connected to Google Calendar", email
            
        except Exception as e:
            return False, f"Authentication failed: {str(e)}", None
    
    def get_credentials(self) -> Optional[Credentials]:
        """
        Get valid credentials from stored token.
        
        Returns:
            Valid Credentials object or None if not authenticated
        """
        if not os.path.exists(self.token_file):
            return None
        
        try:
            credentials = Credentials.from_authorized_user_file(
                self.token_file, 
                self.scopes
            )
            
            # Refresh if expired
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_tokens(credentials)
            
            # Check if valid
            if credentials and credentials.valid:
                return credentials
                
            return None
            
        except Exception:
            return None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return self.get_credentials() is not None
    
    def get_calendar_service(self):
        """
        Get authenticated Google Calendar service.
        
        Returns:
            Google Calendar API service or None
        """
        credentials = self.get_credentials()
        if not credentials:
            return None
        
        return build("calendar", "v3", credentials=credentials)
    
    def get_status(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get current authentication status.
        
        Returns:
            Tuple of (connected, email, calendar_id)
        """
        credentials = self.get_credentials()
        if not credentials:
            return False, None, None
        
        email = self._get_user_email(credentials)
        return True, email, "primary"
    
    def disconnect(self) -> Tuple[bool, str]:
        """
        Disconnect by removing stored tokens.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            return True, "Successfully disconnected from Google Calendar"
        except Exception as e:
            return False, f"Failed to disconnect: {str(e)}"
    
    def _save_tokens(self, credentials: Credentials) -> None:
        """Save credentials to token file."""
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        
        with open(self.token_file, "w") as f:
            json.dump(token_data, f)
    
    def _get_user_email(self, credentials: Credentials) -> Optional[str]:
        """Get user email from credentials."""
        try:
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info.get("email")
        except Exception:
            return None


# Global auth manager instance
auth_manager = GoogleAuthManager()