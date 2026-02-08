"""
Minimal unit tests for calendar service.

Tests cover:
- Availability checking
- Appointment creation/cancellation
- Calendar MCP integration points
"""

from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

import calendar_service
import database


class TestCheckAvailability:
    """Tests for calendar availability checking"""

    def test_check_availability_success(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test checking availability with valid user"""
        # Execute
        result = calendar_service.check_availability(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            date="2026-02-15"
        )

        # Assert
        assert result["success"] is True
        assert result["date"] == "2026-02-15"
        assert "available_slots" in result
        assert isinstance(result["available_slots"], list)

    def test_check_availability_no_oauth_token(
        self,
        db_session: Session,
        sample_user: database.User
    ):
        """Test checking availability without OAuth token"""
        # Execute
        result = calendar_service.check_availability(
            user_id=sample_user.id,
            db=db_session,
            date="2026-02-15"
        )

        # Assert
        assert result["success"] is False
        assert "error" in result

    def test_check_availability_nonexistent_user(self, db_session: Session):
        """Test checking availability for non-existent user"""
        # Execute
        result = calendar_service.check_availability(
            user_id="user_nonexistent",
            db=db_session,
            date="2026-02-15"
        )

        # Assert
        assert result["success"] is False


class TestBookAppointment:
    """Tests for appointment booking"""

    def test_book_appointment_success(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test successful appointment booking"""
        # Execute
        result = calendar_service.book_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            patient_name="John Doe",
            patient_phone="+12025551234",
            date="2026-02-15",
            time="14:00",
            appointment_type="General Checkup"
        )

        # Assert
        assert result["success"] is True
        assert "appointment_id" in result
        assert "confirmation_number" in result
        assert "message" in result

    def test_book_appointment_creates_patient(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test that booking creates patient if doesn't exist"""
        # Execute
        result = calendar_service.book_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            patient_name="New Patient",
            patient_phone="+12025559999",
            date="2026-02-15",
            time="15:00"
        )

        # Assert
        assert result["success"] is True

        # Verify patient was created
        patient = db_session.query(database.Patient).filter(
            database.Patient.phone == "+12025559999"
        ).first()
        assert patient is not None
        assert patient.name == "New Patient"

    def test_book_appointment_no_oauth_token(
        self,
        db_session: Session,
        sample_user: database.User
    ):
        """Test booking without OAuth token"""
        # Execute
        result = calendar_service.book_appointment(
            user_id=sample_user.id,
            db=db_session,
            patient_name="John Doe",
            patient_phone="+12025551234",
            date="2026-02-15",
            time="14:00"
        )

        # Assert
        assert result["success"] is False
        assert "error" in result

    def test_book_appointment_creates_database_record(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test that booking creates appointment in database"""
        # Execute
        result = calendar_service.book_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            patient_name="Test Patient",
            patient_phone="+12025558888",
            date="2026-02-15",
            time="16:00"
        )

        # Assert
        appointment = db_session.query(database.Appointment).filter(
            database.Appointment.id == result["appointment_id"]
        ).first()
        assert appointment is not None
        assert appointment.status == "scheduled"
        assert appointment.reminder_sent is False


class TestCancelAppointment:
    """Tests for appointment cancellation"""

    def test_cancel_appointment_success(
        self,
        db_session: Session,
        sample_appointment: database.Appointment,
        sample_user_with_oauth: database.User
    ):
        """Test successful appointment cancellation"""
        # Execute
        result = calendar_service.cancel_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            appointment_id=sample_appointment.id
        )

        # Assert
        assert result["success"] is True

    def test_cancel_appointment_updates_status(
        self,
        db_session: Session,
        sample_appointment: database.Appointment,
        sample_user_with_oauth: database.User
    ):
        """Test that cancellation updates appointment status"""
        # Execute
        calendar_service.cancel_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            appointment_id=sample_appointment.id
        )

        # Assert - check status was updated
        updated = db_session.query(database.Appointment).filter(
            database.Appointment.id == sample_appointment.id
        ).first()
        assert updated.status == "cancelled"

    def test_cancel_appointment_nonexistent(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test cancelling non-existent appointment"""
        # Execute
        result = calendar_service.cancel_appointment(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            appointment_id="appt_nonexistent"
        )

        # Assert
        assert result["success"] is False


class TestGetUpcomingAppointments:
    """Tests for getting upcoming appointments"""

    def test_get_upcoming_appointments_empty(
        self,
        db_session: Session,
        sample_user: database.User
    ):
        """Test getting upcoming appointments when none exist"""
        # Execute
        appointments = calendar_service.get_upcoming_appointments(
            user_id=sample_user.id,
            db=db_session
        )

        # Assert
        assert isinstance(appointments, list)
        assert len(appointments) == 0

    def test_get_upcoming_appointments_includes_scheduled(
        self,
        db_session: Session,
        sample_appointment: database.Appointment,
        sample_user: database.User
    ):
        """Test that upcoming appointments includes scheduled appointments"""
        # Execute
        appointments = calendar_service.get_upcoming_appointments(
            user_id=sample_user.id,
            db=db_session
        )

        # Assert
        assert len(appointments) > 0
        assert appointments[0]["id"] == sample_appointment.id
        assert appointments[0]["patient_name"] == "John Doe"

    def test_get_upcoming_appointments_respects_days_ahead(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test that days_ahead parameter is respected"""
        # Setup - create appointment far in future
        from datetime import datetime, timedelta
        future_date = (datetime.utcnow() + timedelta(days=60)).strftime("%Y-%m-%d")

        appointment = database.Appointment(
            id="appt_future",
            doctor_id=sample_user_with_oauth.id,
            patient_id="pat_test",
            date=future_date,
            time="14:00",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()

        # Execute - with days_ahead=30
        appointments = calendar_service.get_upcoming_appointments(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            days_ahead=30
        )

        # Assert - far future appointment should not be included
        appointment_ids = [a["id"] for a in appointments]
        assert "appt_future" not in appointment_ids


class TestCalendarMCPIntegration:
    """Tests for Calendar MCP integration points"""

    def test_call_calendar_mcp_with_oauth_token(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test that call_calendar_mcp is called with OAuth token"""
        # Execute
        result = calendar_service.call_calendar_mcp(
            user_id=sample_user_with_oauth.id,
            db=db_session,
            operation="list_events",
            date="2026-02-15"
        )

        # Assert
        assert result is not None
        assert result["success"] is True
        assert result["operation"] == "list_events"

    def test_call_calendar_mcp_missing_token(
        self,
        db_session: Session,
        sample_user: database.User
    ):
        """Test call_calendar_mcp with missing OAuth token"""
        # Execute & Assert
        with pytest.raises(calendar_service.CalendarServiceError):
            calendar_service.call_calendar_mcp(
                user_id=sample_user.id,
                db=db_session,
                operation="list_events"
            )

    def test_call_calendar_mcp_nonexistent_user(self, db_session: Session):
        """Test call_calendar_mcp with non-existent user"""
        # Execute & Assert
        with pytest.raises(calendar_service.CalendarServiceError):
            calendar_service.call_calendar_mcp(
                user_id="user_nonexistent",
                db=db_session,
                operation="list_events"
            )


class TestCalendarServiceErrors:
    """Tests for error handling in calendar service"""

    def test_check_availability_handles_exception(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test error handling in check_availability"""
        # Setup - mock call_calendar_mcp to raise exception
        with patch("calendar_service.call_calendar_mcp") as mock_call:
            mock_call.side_effect = calendar_service.CalendarServiceError("MCP Error")

            # Execute
            result = calendar_service.check_availability(
                user_id=sample_user_with_oauth.id,
                db=db_session,
                date="2026-02-15"
            )

            # Assert
            assert result["success"] is False
            assert "error" in result

    def test_book_appointment_handles_exception(
        self,
        db_session: Session,
        sample_user_with_oauth: database.User
    ):
        """Test error handling in book_appointment"""
        # Setup - mock call_calendar_mcp to raise exception
        with patch("calendar_service.call_calendar_mcp") as mock_call:
            mock_call.side_effect = calendar_service.CalendarServiceError("MCP Error")

            # Execute
            result = calendar_service.book_appointment(
                user_id=sample_user_with_oauth.id,
                db=db_session,
                patient_name="Test",
                patient_phone="+12025551234",
                date="2026-02-15",
                time="14:00"
            )

            # Assert
            assert result["success"] is False
