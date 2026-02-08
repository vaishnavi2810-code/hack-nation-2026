"""
Unit tests for Google OAuth integration.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

from src import config
from src.auth import service as auth_service
from src.database import models as db_models


class TestGetGoogleOAuthUrl:
    """Tests for getting Google OAuth URL"""

    def test_get_google_oauth_url_success(self):
        """Test getting OAuth URL"""
        pytest.skip("Google OAuth requires credentials.json - skipped for dummy calendar testing")


class TestCreateOrUpdateUser:
    """Tests for user creation/update with OAuth"""

    def test_create_user_with_oauth(self, db_session: Session):
        """Test creating user with OAuth token"""
        oauth_data = {
            "access_token": "ya29.test_token",
            "refresh_token": "1//test_refresh",
            "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar"]
        }
        
        user = auth_service.create_or_update_user(
            db=db_session,
            email="newuser@example.com",
            name="New User",
            oauth_token_data=oauth_data
        )
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.google_oauth_token is not None

    def test_update_user_with_new_oauth(self, db_session: Session, sample_user_with_oauth):
        """Test updating user with new OAuth token"""
        new_oauth_data = {
            "access_token": "ya29.new_token",
            "refresh_token": "1//new_refresh",
            "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar"]
        }
        
        updated_user = auth_service.create_or_update_user(
            db=db_session,
            email=sample_user_with_oauth.email,
            name=sample_user_with_oauth.name,
            oauth_token_data=new_oauth_data
        )
        
        assert updated_user is not None
        token_data = json.loads(updated_user.google_oauth_token)
        assert token_data["access_token"] == "ya29.new_token"


class TestGetUserOAuthToken:
    """Tests for retrieving user OAuth tokens"""

    def test_get_valid_oauth_token(self, db_session: Session, sample_user_with_oauth):
        """Test getting valid OAuth token"""
        token_data = auth_service.get_user_oauth_token(
            db=db_session,
            user_id=sample_user_with_oauth.id
        )
        
        assert token_data is not None
        assert "access_token" in token_data
        assert token_data["access_token"] == "ya29.test_access_token_12345"

    def test_get_oauth_token_user_not_found(self, db_session: Session):
        """Test getting token for non-existent user"""
        token_data = auth_service.get_user_oauth_token(
            db=db_session,
            user_id="nonexistent_user"
        )
        
        assert token_data is None


class TestOAuthTokenRefresh:
    """Tests for OAuth token refresh"""

    def test_token_refresh_integration(self):
        """Test token refresh mechanism"""
        pytest.skip("OAuth refresh requires Google credentials file - skipped for dummy calendar testing")
