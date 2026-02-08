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

import database


class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, db_session: Session):
        """Test creating a user"""
        # Execute
        user = database.User(
            id="user_test",
            email="test@example.com",
            name="Test User",
            phone="+12025551234"
        )
        db_session.add(user)
        db_session.commit()

        # Assert
        assert user.id == "user_test"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_oauth_token_storage(self, db_session: Session):
        """Test storing OAuth token in user"""
        # Execute
        import json
        oauth_token = {
            "access_token": "test_token",
            "refresh_token": "refresh_token"
        }
        user = database.User(
            id="user_oauth",
            email="oauth@example.com",
            name="OAuth User",
            google_oauth_token=json.dumps(oauth_token)
        )
        db_session.add(user)
        db_session.commit()

        # Assert
        stored_token = json.loads(user.google_oauth_token)
        assert stored_token["access_token"] == "test_token"


class TestPatientModel:
    """Tests for Patient model"""

    def test_create_patient(self, db_session: Session, sample_user: database.User):
        """Test creating a patient"""
        # Execute
        patient = database.Patient(
            id="pat_test",
            doctor_id=sample_user.id,
            name="John Doe",
            phone="+12025551111",
            email="patient@example.com"
        )
        db_session.add(patient)
        db_session.commit()

        # Assert
        assert patient.id == "pat_test"
        assert patient.name == "John Doe"
        assert patient.doctor_id == sample_user.id
        assert patient.created_at is not None

    def test_patient_doctor_relationship(self, db_session: Session, sample_patient: database.Patient):
        """Test patient-doctor relationship"""
        # Execute
        doctor = sample_patient.doctor

        # Assert
        assert doctor is not None
        assert doctor.id == sample_patient.doctor_id


class TestAppointmentModel:
    """Tests for Appointment model"""

    def test_create_appointment(
        self,
        db_session: Session,
        sample_user: database.User,
        sample_patient: database.Patient
    ):
        """Test creating an appointment"""
        # Execute
        appointment = database.Appointment(
            id="appt_test",
            doctor_id=sample_user.id,
            patient_id=sample_patient.id,
            date="2026-02-15",
            time="14:00",
            duration_minutes=30,
            type="General Checkup"
        )
        db_session.add(appointment)
        db_session.commit()

        # Assert
        assert appointment.status == "scheduled"
        assert appointment.reminder_sent is False
        assert appointment.duration_minutes == 30

    def test_appointment_relationships(self, db_session: Session, sample_appointment: database.Appointment):
        """Test appointment relationships"""
        # Execute
        doctor = sample_appointment.doctor
        patient = sample_appointment.patient

        # Assert
        assert doctor is not None
        assert patient is not None
        assert patient.name == "John Doe"


class TestCallModel:
    """Tests for Call model"""

    def test_create_call(self, db_session: Session, sample_user: database.User):
        """Test creating a call record"""
        # Execute
        call = database.Call(
            id="call_test",
            doctor_id=sample_user.id,
            call_sid="CA123456789abcdef",
            direction="inbound",
            type="booking",
            phone_number="+12025551111",
            status="completed"
        )
        db_session.add(call)
        db_session.commit()

        # Assert
        assert call.id == "call_test"
        assert call.direction == "inbound"
        assert call.doctor_id == sample_user.id


class TestUserSessionModel:
    """Tests for UserSession model"""

    def test_create_session(self, db_session: Session, sample_user: database.User):
        """Test creating a user session"""
        # Execute
        session = database.UserSession(
            id="sess_test",
            user_id=sample_user.id,
            access_token="jwt_access_token",
            refresh_token="jwt_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(session)
        db_session.commit()

        # Assert
        assert session.id == "sess_test"
        assert session.is_active is True
        assert session.access_token == "jwt_access_token"


class TestDatabaseConstraints:
    """Tests for database constraints"""

    def test_user_email_unique(self, db_session: Session):
        """Test that user email must be unique"""
        # Setup
        user1 = database.User(
            id="user1",
            email="duplicate@example.com",
            name="User 1"
        )
        db_session.add(user1)
        db_session.commit()

        # Execute - create user with same email
        user2 = database.User(
            id="user2",
            email="duplicate@example.com",
            name="User 2"
        )
        db_session.add(user2)

        # Assert - should raise IntegrityError
        import sqlalchemy
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.commit()

    def test_patient_requires_doctor(self, db_session: Session):
        """Test that patient must have a doctor"""
        # Execute - create patient without doctor_id
        patient = database.Patient(
            id="pat_no_doctor",
            doctor_id=None,  # ← Missing doctor
            name="Orphan Patient",
            phone="+1234567890"
        )
        db_session.add(patient)

        # Assert - should raise error on commit
        import sqlalchemy
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.commit()
