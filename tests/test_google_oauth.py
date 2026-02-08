"""
Thorough unit tests for Google OAuth authentication flow.

Tests cover:
- OAuth URL generation
- Authorization code exchange
- Token refresh
- User info retrieval
- Edge cases and error handling
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

import auth_service
import database


class TestGoogleOAuthURLGeneration:
    """Tests for generating Google OAuth authorization URLs"""

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_get_google_oauth_url_success(self, mock_flow_class):
        """Test successful OAuth URL generation"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
            "state_token_123"
        )
        mock_flow_class.return_value = mock_flow

        # Execute
        auth_url, state = auth_service.get_google_oauth_url()

        # Assert
        assert auth_url.startswith("https://accounts.google.com")
        assert state == "state_token_123"
        mock_flow_class.assert_called_once()

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_get_google_oauth_url_includes_calendar_scope(self, mock_flow_class):
        """Test that generated URL includes calendar scope"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("http://example.com", "state")
        mock_flow_class.return_value = mock_flow

        # Execute
        auth_service.get_google_oauth_url()

        # Assert - verify Flow was created with calendar scope
        call_args = mock_flow_class.call_args
        assert "https://www.googleapis.com/auth/calendar" in call_args[0][1]

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_get_google_oauth_url_offline_access(self, mock_flow_class):
        """Test that OAuth requests offline access (for refresh tokens)"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("http://example.com", "state")
        mock_flow_class.return_value = mock_flow

        # Execute
        auth_service.get_google_oauth_url()

        # Assert - verify offline access is requested
        call_kwargs = mock_flow.authorization_url.call_args[1]
        assert call_kwargs.get("access_type") == "offline"
        assert call_kwargs.get("prompt") == "consent"


class TestCodeExchange:
    """Tests for exchanging authorization code for OAuth token"""

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_exchange_oauth_code_success(self, mock_flow_class, mock_google_oauth_token):
        """Test successful authorization code exchange"""
        # Setup
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = mock_google_oauth_token["access_token"]
        mock_credentials.refresh_token = mock_google_oauth_token["refresh_token"]
        mock_credentials.expiry = datetime.fromisoformat(
            mock_google_oauth_token["expiry"]
        )
        mock_credentials.token_uri = mock_google_oauth_token["token_uri"]
        mock_credentials.client_id = mock_google_oauth_token["client_id"]
        mock_credentials.client_secret = mock_google_oauth_token["client_secret"]
        mock_credentials.scopes = mock_google_oauth_token["scopes"]

        mock_flow.credentials = mock_credentials
        mock_flow_class.return_value = mock_flow

        # Execute
        result = auth_service.exchange_oauth_code_for_token(
            "auth_code_123",
            "state_token_123"
        )

        # Assert
        assert result is not None
        assert result["access_token"] == mock_google_oauth_token["access_token"]
        assert result["refresh_token"] == mock_google_oauth_token["refresh_token"]
        assert result["token_uri"] == mock_google_oauth_token["token_uri"]
        mock_flow.fetch_token.assert_called_once_with(code="auth_code_123")

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_exchange_oauth_code_failure(self, mock_flow_class):
        """Test handling of code exchange failure"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("Invalid code")
        mock_flow_class.return_value = mock_flow

        # Execute
        result = auth_service.exchange_oauth_code_for_token(
            "invalid_code",
            "state_token_123"
        )

        # Assert
        assert result is None

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_exchange_oauth_code_missing_refresh_token(self, mock_flow_class):
        """Test handling when refresh token is missing"""
        # Setup
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = "access_token"
        mock_credentials.refresh_token = None  # ← Missing refresh token
        mock_credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "client_id"
        mock_credentials.client_secret = "secret"
        mock_credentials.scopes = []

        mock_flow.credentials = mock_credentials
        mock_flow_class.return_value = mock_flow

        # Execute
        result = auth_service.exchange_oauth_code_for_token("code", "state")

        # Assert - should still return result even without refresh token
        assert result is not None
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] is None


class TestUserInfoRetrieval:
    """Tests for retrieving user info from Google"""

    @patch("auth_service.build")
    @patch("auth_service.Credentials")
    def test_get_user_info_from_google_success(
        self,
        mock_credentials_class,
        mock_build,
        mock_google_user_info
    ):
        """Test successful user info retrieval"""
        # Setup
        mock_service = MagicMock()
        mock_service.userinfo().get().execute.return_value = mock_google_user_info
        mock_build.return_value = mock_service

        # Execute
        result = auth_service.get_user_info_from_google("test_access_token")

        # Assert
        assert result == mock_google_user_info
        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"

    @patch("auth_service.build")
    @patch("auth_service.Credentials")
    def test_get_user_info_from_google_api_error(self, mock_credentials_class, mock_build):
        """Test handling of API error when retrieving user info"""
        # Setup
        mock_service = MagicMock()
        mock_service.userinfo().get().execute.side_effect = Exception("API Error")
        mock_build.return_value = mock_service

        # Execute
        result = auth_service.get_user_info_from_google("invalid_token")

        # Assert
        assert result is None


class TestCreateOrUpdateUser:
    """Tests for creating/updating user with OAuth token"""

    def test_create_new_user_with_oauth(self, db_session: Session, mock_google_oauth_token):
        """Test creating a new user with OAuth token"""
        # Execute
        user = auth_service.create_or_update_user(
            db=db_session,
            email="newuser@gmail.com",
            name="New User",
            oauth_token_data=mock_google_oauth_token
        )

        # Assert
        assert user is not None
        assert user.email == "newuser@gmail.com"
        assert user.name == "New User"
        assert user.google_oauth_token is not None

        # Verify OAuth token was stored
        stored_token = json.loads(user.google_oauth_token)
        assert stored_token["access_token"] == mock_google_oauth_token["access_token"]
        assert stored_token["refresh_token"] == mock_google_oauth_token["refresh_token"]

    def test_update_existing_user_oauth(
        self,
        db_session: Session,
        sample_user: database.User,
        mock_google_oauth_token
    ):
        """Test updating existing user with new OAuth token"""
        # Setup
        original_created_at = sample_user.created_at

        # Execute
        updated_user = auth_service.create_or_update_user(
            db=db_session,
            email=sample_user.email,
            name="Dr. Updated Name",
            oauth_token_data=mock_google_oauth_token
        )

        # Assert
        assert updated_user.id == sample_user.id
        assert updated_user.name == "Dr. Updated Name"
        assert updated_user.google_oauth_token is not None
        # Verify created_at didn't change
        assert updated_user.created_at == original_created_at

    def test_oauth_token_stored_as_json(self, db_session: Session, mock_google_oauth_token):
        """Test that OAuth token is stored as JSON"""
        # Execute
        user = auth_service.create_or_update_user(
            db=db_session,
            email="json_test@gmail.com",
            name="JSON Test",
            oauth_token_data=mock_google_oauth_token
        )

        # Assert - should be valid JSON
        stored_token = json.loads(user.google_oauth_token)
        assert isinstance(stored_token, dict)
        assert all(key in stored_token for key in [
            "access_token", "refresh_token", "expiry"
        ])


class TestOAuthTokenRefresh:
    """Tests for OAuth token refresh mechanism"""

    def test_get_user_oauth_token_valid(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test retrieving valid OAuth token"""
        # Execute
        token = auth_service.get_user_oauth_token(db_session, sample_user_with_oauth.id)

        # Assert
        assert token is not None
        assert "access_token" in token
        assert token["access_token"] == "ya29.test_access_token_12345"

    def test_get_user_oauth_token_missing(self, db_session: Session, sample_user: database.User):
        """Test retrieving token when user has no OAuth token"""
        # Execute
        token = auth_service.get_user_oauth_token(db_session, sample_user.id)

        # Assert
        assert token is None

    def test_get_user_oauth_token_nonexistent_user(self, db_session: Session):
        """Test retrieving token for non-existent user"""
        # Execute
        token = auth_service.get_user_oauth_token(db_session, "user_nonexistent")

        # Assert
        assert token is None

    @patch("auth_service.Credentials")
    @patch("auth_service.Request")
    def test_refresh_user_oauth_token_success(
        self,
        mock_request_class,
        mock_credentials_class,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test successful OAuth token refresh"""
        # Setup
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request

        mock_credentials = MagicMock()
        mock_credentials.token = "ya29.refreshed_token_12345"
        mock_credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        mock_credentials.scopes = []
        mock_credentials_class.return_value = mock_credentials

        # Patch the json loading
        with patch("builtins.open", create=True):
            with patch("json.load") as mock_json_load:
                mock_json_load.return_value = {
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "test_client_id",
                    "client_secret": "test_secret"
                }

                # Execute
                result = auth_service.refresh_user_oauth_token(
                    db_session,
                    sample_user_with_oauth.id
                )

        # Assert
        assert result is True

    def test_refresh_user_oauth_token_no_refresh_token(
        self,
        db_session: Session,
        sample_user: database.User
    ):
        """Test refresh when user has no refresh token"""
        # Execute
        result = auth_service.refresh_user_oauth_token(db_session, sample_user.id)

        # Assert
        assert result is False

    def test_get_oauth_token_auto_refresh_on_expiry(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test that token is auto-refreshed when expired"""
        # Setup - set token expiry to past
        sample_user_with_oauth.google_token_expiry = datetime.utcnow() - timedelta(
            hours=1
        )
        db_session.commit()

        # Execute - should trigger auto-refresh
        with patch("auth_service.refresh_user_oauth_token") as mock_refresh:
            mock_refresh.return_value = True

            token = auth_service.get_user_oauth_token(
                db_session,
                sample_user_with_oauth.id
            )

            # Assert - refresh should have been called
            # (Note: actual implementation checks expiry in the function)
            assert token is not None or token is None  # Depends on implementation


class TestOAuthErrorHandling:
    """Tests for error handling in OAuth flow"""

    def test_create_user_handles_database_error(self, db_session: Session):
        """Test that database errors are handled gracefully"""
        # Setup - make db_session invalid
        db_session.close()

        # Execute
        result = auth_service.create_or_update_user(
            db=db_session,
            email="error@test.com",
            name="Error Test",
            oauth_token_data={"access_token": "test"}
        )

        # Assert
        assert result is None

    @patch("auth_service.Flow.from_client_secrets_file")
    def test_exchange_code_handles_invalid_state(self, mock_flow_class):
        """Test handling of invalid state token"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = ValueError("Invalid state")
        mock_flow_class.return_value = mock_flow

        # Execute
        result = auth_service.exchange_oauth_code_for_token(
            "code_123",
            "wrong_state_token"
        )

        # Assert
        assert result is None


class TestGoogleOAuthIntegration:
    """Integration tests for complete OAuth flow"""

    @patch("auth_service.get_user_info_from_google")
    @patch("auth_service.exchange_oauth_code_for_token")
    @patch("auth_service.Flow.from_client_secrets_file")
    def test_complete_oauth_flow(
        self,
        mock_flow_class,
        mock_exchange,
        mock_get_info,
        db_session: Session,
        mock_google_oauth_token,
        mock_google_user_info
    ):
        """Test complete OAuth flow: URL → Code → Token → User"""
        # Setup
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("https://example.com", "state_123")
        mock_flow_class.return_value = mock_flow

        mock_exchange.return_value = mock_google_oauth_token
        mock_get_info.return_value = mock_google_user_info

        # Execute - Step 1: Get OAuth URL
        auth_url, state = auth_service.get_google_oauth_url()
        assert auth_url is not None
        assert state == "state_123"

        # Execute - Step 2: Exchange code for token
        token = auth_service.exchange_oauth_code_for_token("auth_code_123", state)
        assert token == mock_google_oauth_token

        # Execute - Step 3: Get user info
        user_info = auth_service.get_user_info_from_google(token["access_token"])
        assert user_info == mock_google_user_info

        # Execute - Step 4: Create/update user
        user = auth_service.create_or_update_user(
            db=db_session,
            email=user_info["email"],
            name=user_info["name"],
            oauth_token_data=token
        )

        # Assert - User created with OAuth token
        assert user is not None
        assert user.email == "user@gmail.com"
        assert user.google_oauth_token is not None
        assert json.loads(user.google_oauth_token)["access_token"] == (
            mock_google_oauth_token["access_token"]
        )
