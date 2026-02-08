"""
Minimal unit tests for JWT and session management functions.

Tests cover:
- JWT token generation and validation
- Session creation and invalidation
- User lookup and management
"""

from datetime import datetime, timedelta
from jose import jwt
import pytest
from sqlalchemy.orm import Session

import config
import auth_service
import database


class TestJWTTokens:
    """Tests for JWT token generation and validation"""

    def test_create_access_token(self):
        """Test access token creation"""
        # Execute
        data = {"user_id": "user_123"}
        token = auth_service.create_access_token(data)

        # Assert
        assert token is not None
        assert isinstance(token, str)

        # Verify token can be decoded
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        assert payload["user_id"] == "user_123"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """Test access token with custom expiry"""
        # Execute
        data = {"user_id": "user_123"}
        custom_expiry = timedelta(minutes=60)
        token = auth_service.create_access_token(data, custom_expiry)

        # Assert
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        assert payload["user_id"] == "user_123"

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        # Execute
        token = auth_service.create_refresh_token("user_123")

        # Assert
        assert token is not None
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        assert payload["user_id"] == "user_123"
        assert payload["type"] == "refresh"

    def test_verify_token_valid(self):
        """Test verification of valid token"""
        # Setup
        data = {"user_id": "user_123"}
        token = auth_service.create_access_token(data)

        # Execute
        payload = auth_service.verify_token(token)

        # Assert
        assert payload is not None
        assert payload["user_id"] == "user_123"

    def test_verify_token_invalid(self):
        """Test verification of invalid token"""
        # Execute
        payload = auth_service.verify_token("invalid_token_xyz")

        # Assert
        assert payload is None

    def test_verify_token_expired(self):
        """Test verification of expired token"""
        # Setup
        data = {"user_id": "user_123"}
        expired_expiry = timedelta(hours=-1)  # Expired 1 hour ago
        token = auth_service.create_access_token(data, expired_expiry)

        # Execute
        payload = auth_service.verify_token(token)

        # Assert
        assert payload is None


class TestUserManagement:
    """Tests for user lookup and creation"""

    def test_get_user_by_id(self, db_session: Session, sample_user: database.User):
        """Test getting user by ID"""
        # Execute
        user = auth_service.get_user_by_id(db_session, sample_user.id)

        # Assert
        assert user is not None
        assert user.email == sample_user.email
        assert user.id == sample_user.id

    def test_get_user_by_id_nonexistent(self, db_session: Session):
        """Test getting non-existent user by ID"""
        # Execute
        user = auth_service.get_user_by_id(db_session, "user_nonexistent")

        # Assert
        assert user is None

    def test_get_user_by_email(self, db_session: Session, sample_user: database.User):
        """Test getting user by email"""
        # Execute
        user = auth_service.get_user_by_email(db_session, sample_user.email)

        # Assert
        assert user is not None
        assert user.id == sample_user.id

    def test_get_user_by_email_nonexistent(self, db_session: Session):
        """Test getting non-existent user by email"""
        # Execute
        user = auth_service.get_user_by_email(db_session, "nonexistent@example.com")

        # Assert
        assert user is None


class TestSessionManagement:
    """Tests for user session creation and invalidation"""

    def test_create_session(self, db_session: Session, sample_user: database.User):
        """Test session creation"""
        # Execute
        session = auth_service.create_session(db_session, sample_user.id)

        # Assert
        assert session is not None
        assert session.user_id == sample_user.id
        assert session.is_active is True
        assert session.access_token is not None
        assert session.refresh_token is not None

    def test_create_session_tokens_are_jwt(self, db_session: Session, sample_user: database.User):
        """Test that session tokens are valid JWT"""
        # Setup
        session = auth_service.create_session(db_session, sample_user.id)

        # Execute
        access_payload = auth_service.verify_token(session.access_token)
        refresh_payload = auth_service.verify_token(session.refresh_token)

        # Assert
        assert access_payload is not None
        assert access_payload["user_id"] == sample_user.id
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"

    def test_get_session(self, db_session: Session, sample_user: database.User):
        """Test getting active session"""
        # Setup
        created_session = auth_service.create_session(db_session, sample_user.id)

        # Execute
        retrieved_session = auth_service.get_session(db_session, created_session.id)

        # Assert
        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.is_active is True

    def test_get_session_nonexistent(self, db_session: Session):
        """Test getting non-existent session"""
        # Execute
        session = auth_service.get_session(db_session, "sess_nonexistent")

        # Assert
        assert session is None

    def test_get_session_inactive(self, db_session: Session, sample_user: database.User):
        """Test getting inactive session"""
        # Setup
        session = auth_service.create_session(db_session, sample_user.id)
        session.is_active = False
        db_session.commit()

        # Execute
        retrieved = auth_service.get_session(db_session, session.id)

        # Assert
        assert retrieved is None

    def test_get_session_expired(self, db_session: Session, sample_user: database.User):
        """Test getting expired session"""
        # Setup
        session = auth_service.create_session(db_session, sample_user.id)
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        # Execute
        retrieved = auth_service.get_session(db_session, session.id)

        # Assert
        assert retrieved is None

    def test_invalidate_session(self, db_session: Session, sample_user: database.User):
        """Test session invalidation"""
        # Setup
        session = auth_service.create_session(db_session, sample_user.id)

        # Execute
        result = auth_service.invalidate_session(db_session, session.id)

        # Assert
        assert result is True
        retrieved = auth_service.get_session(db_session, session.id)
        assert retrieved is None

    def test_invalidate_session_nonexistent(self, db_session: Session):
        """Test invalidating non-existent session"""
        # Execute
        result = auth_service.invalidate_session(db_session, "sess_nonexistent")

        # Assert
        assert result is False


class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        # Execute
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > len(password)

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        # Setup
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        # Execute
        result = auth_service.verify_password(password, hashed)

        # Assert
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        # Setup
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        # Execute
        result = auth_service.verify_password("wrong_password", hashed)

        # Assert
        assert result is False
