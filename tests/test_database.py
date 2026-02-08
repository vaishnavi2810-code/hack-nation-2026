"""
Minimal unit tests for database models.

Tests cover:
- Model creation and relationships
- Required fields
- Constraints
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.database import models as db_models
from src import config


class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, db_session: Session):
        """Test creating a user"""
        user = db_models.User(
            id="user_test_123",
            email="test@example.com",
            name="Test User",
            phone="+12025551234",
            timezone="UTC"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id == "user_test_123"
        assert user.email == "test@example.com"

    def test_user_oauth_token_storage(self, db_session: Session):
        """Test storing OAuth token in user"""
        import json
        oauth_data = {
            "access_token": "ya29.test",
            "refresh_token": "1//test",
            "expiry": "2026-02-15T10:00:00"
        }
        
        user = db_models.User(
            id="user_oauth_123",
            email="oauth@example.com",
            name="OAuth User",
            google_oauth_token=json.dumps(oauth_data),
            google_refresh_token=oauth_data["refresh_token"]
        )
        db_session.add(user)
        db_session.commit()
        
        stored_user = db_session.query(db_models.User).filter_by(id="user_oauth_123").first()
        assert stored_user.google_oauth_token is not None
        assert json.loads(stored_user.google_oauth_token)["access_token"] == "ya29.test"


class TestPatientModel:
    """Tests for Patient model"""

    def test_create_patient(self, db_session: Session, sample_user):
        """Test creating a patient"""
        patient = db_models.Patient(
            id="pat_test_123",
            doctor_id=sample_user.id,
            name="John Doe",
            phone="+12025551234"
        )
        db_session.add(patient)
        db_session.commit()
        
        assert patient.id == "pat_test_123"
        assert patient.doctor_id == sample_user.id

    def test_patient_doctor_relationship(self, db_session: Session, sample_user):
        """Test patient-doctor relationship"""
        patient = db_models.Patient(
            id="pat_rel_123",
            doctor_id=sample_user.id,
            name="Jane Doe",
            phone="+12025551235"
        )
        db_session.add(patient)
        db_session.commit()
        
        assert patient.doctor.id == sample_user.id


class TestAppointmentModel:
    """Tests for Appointment model"""

    def test_create_appointment(self, db_session: Session, sample_user, sample_patient):
        """Test creating an appointment"""
        appointment = db_models.Appointment(
            id="appt_test_123",
            doctor_id=sample_user.id,
            patient_id=sample_patient.id,
            date="2026-02-18",
            time="14:00",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()
        
        assert appointment.id == "appt_test_123"
        assert appointment.status == "scheduled"

    def test_appointment_relationships(self, db_session: Session, sample_user, sample_patient):
        """Test appointment relationships"""
        appointment = db_models.Appointment(
            id="appt_rel_123",
            doctor_id=sample_user.id,
            patient_id=sample_patient.id,
            date="2026-02-19",
            time="15:00"
        )
        db_session.add(appointment)
        db_session.commit()
        
        assert appointment.doctor.id == sample_user.id
        assert appointment.patient.id == sample_patient.id


class TestCallModel:
    """Tests for Call model"""

    def test_create_call(self, db_session: Session, sample_user, sample_patient):
        """Test creating a call record"""
        call = db_models.Call(
            id="call_test_123",
            doctor_id=sample_user.id,
            patient_id=sample_patient.id,
            call_sid="CA1234567890",
            direction="inbound",
            type="booking",
            phone_number="+12025551234",
            status="completed"
        )
        db_session.add(call)
        db_session.commit()
        
        assert call.id == "call_test_123"
        assert call.call_sid == "CA1234567890"


class TestUserSessionModel:
    """Tests for UserSession model"""

    def test_create_session(self, db_session: Session, sample_user):
        """Test creating a user session"""
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session = db_models.UserSession(
            id="sess_test_123",
            user_id=sample_user.id,
            access_token="jwt.access.token",
            refresh_token="jwt.refresh.token",
            expires_at=expires_at
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.id == "sess_test_123"
        assert session.is_active is True


class TestDatabaseConstraints:
    """Tests for database constraints"""

    def test_user_email_unique(self, db_session: Session):
        """Test that user email must be unique"""
        user1 = db_models.User(
            id="user_1",
            email="duplicate@example.com",
            name="User 1"
        )
        user2 = db_models.User(
            id="user_2",
            email="duplicate@example.com",
            name="User 2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_patient_requires_doctor(self, db_session: Session):
        """Test that patient must have a doctor"""
        pytest.skip("SQLite in-memory doesn't enforce FK constraints by default in test mode")
