"""
Unit tests for calendar service.
"""

import json
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session

from src import config
from src.calendar import service as calendar_service
from src.database import models as db_models


class TestCheckAvailability:
    """Tests for checking calendar availability"""

    def test_check_availability_success(self, db_session: Session, sample_user_with_oauth):
        """Test checking availability with valid user"""
        result = calendar_service.check_availability(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            date="2026-02-18"
        )

        assert result["success"] is True
        assert result["date"] == "2026-02-18"
        # Tuesday 2/18/2026 should have availability
        assert len(result["available_slots"]) > 0

    def test_check_availability_monday_2_9_no_slots(self, db_session: Session, sample_user_with_oauth):
        """Test that Monday 2/9/2026 has NO availability"""
        result = calendar_service.check_availability(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            date="2026-02-09"
        )

        assert result["success"] is True
        assert result["date"] == "2026-02-09"
        # Monday 2/9/2026 should have NO availability (special dummy calendar rule)
        assert len(result["available_slots"]) == 0

    def test_check_availability_no_oauth_token(self, db_session: Session, sample_user):
        """Test checking availability without OAuth token"""
        result = calendar_service.check_availability(
            user_id=sample_user.id,
            db=db_session,
            date="2026-02-18"
        )

        assert result["success"] is False
        assert "error" in result


class TestBookAppointment:
    """Tests for booking appointments"""

    def test_book_appointment_success(self, db_session: Session, sample_user_with_oauth):
        """Test booking an appointment"""
        result = calendar_service.book_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            patient_name="John Doe",
            patient_phone="+14155552671",
            date="2026-02-18",
            time="14:00"
        )

        assert result["success"] is True
        assert "appointment_id" in result
        assert "confirmation_number" in result
        assert "message" in result

    def test_book_appointment_creates_patient(self, db_session: Session, sample_user_with_oauth):
        """Test that booking appointment creates patient if not exists"""
        phone = "+14155553333"
        result = calendar_service.book_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            patient_name="New Patient",
            patient_phone=phone,
            date="2026-02-18",
            time="15:00"
        )

        assert result["success"] is True

        # Verify patient was created by querying in the same session
        patient = db_session.query(db_models.Patient).filter_by(
            phone=phone,
            doctor_id=sample_user_with_oauth.id
        ).first()
        assert patient is not None
        assert patient.name == "New Patient"


class TestCancelAppointment:
    """Tests for cancelling appointments"""

    def test_cancel_appointment_success(self, db_session: Session, sample_user_with_oauth):
        """Test cancelling an appointment"""
        # Create appointment for this user first
        from src.database import models as db_models
        appointment = db_models.Appointment(
            id="appt_cancel_test_123",
            doctor_id=sample_user_with_oauth.id,
            patient_id="pat_test_123",
            calendar_event_id="google_event_cancel_123",
            date="2026-02-15",
            time="14:00",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()

        result = calendar_service.cancel_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            appointment_id=appointment.id
        )

        assert result["success"] is True
        assert "message" in result

    def test_cancel_appointment_not_found(self, db_session: Session, sample_user_with_oauth):
        """Test cancelling non-existent appointment"""
        result = calendar_service.cancel_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            appointment_id="nonexistent_id"
        )

        assert result["success"] is False


class TestGetUpcomingAppointments:
    """Tests for retrieving upcoming appointments"""

    def test_get_upcoming_appointments(self, db_session: Session, sample_user_with_oauth, sample_patient):
        """Test getting upcoming appointments"""
        # Create an appointment for this user
        from src.database import models as db_models
        appointment = db_models.Appointment(
            id="appt_upcoming_test_123",
            doctor_id=sample_user_with_oauth.id,
            patient_id=sample_patient.id,
            date="2026-02-15",
            time="14:00",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()

        appointments = calendar_service.get_upcoming_appointments(
            user_id=sample_user_with_oauth.id,
            db=db_session
        )

        assert isinstance(appointments, list)
        # Should have the appointment we just created
        assert len(appointments) > 0
        assert appointments[0]["patient_name"] == sample_patient.name
