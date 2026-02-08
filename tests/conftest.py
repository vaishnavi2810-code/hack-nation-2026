"""
Pytest configuration and fixtures for CallPilot tests.

Provides:
- In-memory SQLite database for testing
- FastAPI test client
- Mock Google OAuth responses
- Sample test data (users, patients, appointments)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Configure test environment before imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_12345"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "test_client_id"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "test_client_secret"
os.environ["GOOGLE_CREDENTIALS_PATH"] = "./test_credentials.json"
os.environ["API_BASE_URL"] = "http://localhost:8000"
os.environ["WEBHOOK_URL"] = "http://localhost:8000/api/webhooks/elevenlabs"

import config
import database
import auth_service
from main import app


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def engine():
    """Create test database engine (in-memory SQLite)"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    database.Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)(
        bind=connection
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# FASTAPI TEST CLIENT
# ============================================================================

@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create FastAPI test client"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    return TestClient(app)


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_user(db_session: Session) -> database.User:
    """Create a sample user for testing"""
    user = database.User(
        id="user_test_123",
        email="doctor@example.com",
        name="Dr. Test Smith",
        phone="+12025551234",
        timezone="America/New_York",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_with_oauth(db_session: Session) -> database.User:
    """Create a user with valid OAuth token"""
    oauth_token = {
        "access_token": "ya29.test_access_token_12345",
        "refresh_token": "1//test_refresh_token_12345",
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    }

    user = database.User(
        id="user_oauth_123",
        email="doctor_oauth@example.com",
        name="Dr. OAuth Test",
        phone="+12025551234",
        timezone="America/New_York",
        google_oauth_token=json.dumps(oauth_token),
        google_refresh_token=oauth_token["refresh_token"],
        google_token_expiry=datetime.fromisoformat(oauth_token["expiry"]),
        google_calendar_id="doctor_oauth@gmail.com",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_patient(db_session: Session, sample_user: database.User) -> database.Patient:
    """Create a sample patient"""
    patient = database.Patient(
        id="pat_test_123",
        doctor_id=sample_user.id,
        name="John Doe",
        phone="+12025551111",
        email="patient@example.com",
        notes="Test patient"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def sample_appointment(
    db_session: Session,
    sample_user: database.User,
    sample_patient: database.Patient
) -> database.Appointment:
    """Create a sample appointment"""
    appointment = database.Appointment(
        id="appt_test_123",
        doctor_id=sample_user.id,
        patient_id=sample_patient.id,
        calendar_event_id="google_event_123",
        date="2026-02-15",
        time="14:00",
        duration_minutes=30,
        type="General Checkup",
        status="scheduled",
        reminder_sent=False
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


# ============================================================================
# MOCK GOOGLE OAUTH RESPONSES
# ============================================================================

@pytest.fixture
def mock_google_oauth_token() -> dict:
    """Mock Google OAuth token response"""
    return {
        "access_token": "ya29.mock_access_token_12345",
        "refresh_token": "1//mock_refresh_token_12345",
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test_client_id.apps.googleusercontent.com",
        "client_secret": "test_client_secret",
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    }


@pytest.fixture
def mock_google_user_info() -> dict:
    """Mock Google user info response"""
    return {
        "id": "google_user_123",
        "email": "user@gmail.com",
        "verified_email": True,
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
        "locale": "en"
    }


@pytest.fixture
def mock_jwt_token() -> str:
    """Create a mock JWT token"""
    from jose import jwt
    payload = {
        "user_id": "user_test_123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


# ============================================================================
# CLEANUP
# ============================================================================

def pytest_sessionfinish(session):
    """Clean up after all tests"""
    # Remove test client overrides
    if hasattr(app, "dependency_overrides"):
        app.dependency_overrides.clear()
