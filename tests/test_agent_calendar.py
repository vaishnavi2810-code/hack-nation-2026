"""
Unit tests for agent endpoint calendar functionality.

Tests the calendar service functions as called by the ElevenLabs agent,
focusing on patient phone number lookup, appointment management, and
availability checking.
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database import models as database
from src.calendar import service as calendar_service
from src.auth import service as auth_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_doctor_with_oauth(db_session: Session):
    """Create a doctor with OAuth token for testing"""
    doctor = database.User(
        id="doctor_agent_test",
        email="agent_doctor@test.com",
        name="Dr. Agent Test",
        phone="+1234567890",
        google_oauth_token=json.dumps({
            "access_token": "test_agent_token",
            "refresh_token": "test_agent_refresh",
            "expires_in": 3600
        }),
        google_refresh_token="test_agent_refresh",
        google_calendar_id="test_agent@google.com"
    )
    db_session.add(doctor)
    db_session.commit()
    return doctor


@pytest.fixture
def test_patient(db_session: Session, test_doctor_with_oauth):
    """Create a test patient"""
    patient = database.Patient(
        id="pat_agent_test",
        doctor_id=test_doctor_with_oauth.id,
        name="Agent Test Patient",
        phone="+14155552671"
    )
    db_session.add(patient)
    db_session.commit()
    return patient


# ============================================================================
# CHECK AVAILABILITY TESTS
# ============================================================================

class TestAgentCheckAvailability:
    """Test availability checking as used by ElevenLabs agent"""

    def test_check_availability_weekday_returns_slots(self, db_session: Session, test_doctor_with_oauth):
        """Agent checks availability on a weekday (Tuesday 2/17) - should return 6 slots"""
        result = calendar_service.check_availability(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            date="2026-02-17"
        )

        assert result["success"] is True
        assert result["date"] == "2026-02-17"
        assert len(result["available_slots"]) == 6
        # Verify slot times
        times = [slot["time"] for slot in result["available_slots"]]
        assert "09:00" in times
        assert "14:00" in times
        assert "16:00" in times

    def test_check_availability_monday_2_9_no_slots(self, db_session: Session, test_doctor_with_oauth):
        """Agent checks availability on Monday 2/9 - should return no slots (special rule)"""
        result = calendar_service.check_availability(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            date="2026-02-09"
        )

        assert result["success"] is True
        assert result["date"] == "2026-02-09"
        assert len(result["available_slots"]) == 0

    def test_check_availability_weekend_no_slots(self, db_session: Session, test_doctor_with_oauth):
        """Agent checks availability on Sunday 2/15 - should return no slots"""
        result = calendar_service.check_availability(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            date="2026-02-15"  # Sunday
        )

        assert result["success"] is True
        assert len(result["available_slots"]) == 0

    def test_check_availability_no_oauth_token_fails(self, db_session: Session):
        """Agent tries to check availability for doctor with no OAuth token - should fail"""
        # Create doctor without OAuth token
        doctor_no_oauth = database.User(
            id="doctor_no_oauth",
            email="no_oauth@test.com",
            name="No OAuth Doctor",
            phone="+1234567890"
        )
        db_session.add(doctor_no_oauth)
        db_session.commit()

        result = calendar_service.check_availability(
            user_id=doctor_no_oauth.id,
            db=db_session,
            date="2026-02-17"
        )

        assert result["success"] is False
        assert "OAuth token" in result["error"]


# ============================================================================
# BOOK APPOINTMENT TESTS
# ============================================================================

class TestAgentBookAppointment:
    """Test appointment booking as used by ElevenLabs agent"""

    def test_book_appointment_success(self, db_session: Session, test_doctor_with_oauth):
        """Agent books appointment for new patient - patient created, appointment stored"""
        result = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name="John Agent Test",
            patient_phone="+14155552671",
            date="2026-02-17",
            time="14:00",
            appointment_type="General Checkup"
        )

        assert result["success"] is True
        assert result["appointment_id"] is not None
        assert result["confirmation_number"] is not None
        assert "John Agent Test" in result["message"]
        assert "2026-02-17" in result["message"]
        assert "14:00" in result["message"]

        # Verify patient was created
        patient = db_session.query(database.Patient).filter(
            database.Patient.phone == "+14155552671"
        ).first()
        assert patient is not None
        assert patient.name == "John Agent Test"
        assert patient.doctor_id == test_doctor_with_oauth.id

        # Verify appointment was created
        appointment = db_session.query(database.Appointment).filter(
            database.Appointment.id == result["appointment_id"]
        ).first()
        assert appointment is not None
        assert appointment.date == "2026-02-17"
        assert appointment.time == "14:00"
        assert appointment.status == "scheduled"

    def test_book_appointment_existing_patient(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent books appointment for existing patient - reuses patient record"""
        result = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name="Agent Test Patient",  # Same name
            patient_phone=test_patient.phone,   # Same phone
            date="2026-02-18",
            time="10:00",
            appointment_type="Follow-up"
        )

        assert result["success"] is True

        # Verify no new patient was created (still only one with this phone)
        patients_with_phone = db_session.query(database.Patient).filter(
            database.Patient.phone == test_patient.phone
        ).all()
        assert len(patients_with_phone) == 1
        assert patients_with_phone[0].id == test_patient.id

    def test_book_appointment_multiple_for_same_patient(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent books multiple appointments for same patient"""
        # Book first appointment
        result1 = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name=test_patient.name,
            patient_phone=test_patient.phone,
            date="2026-02-17",
            time="09:00",
            appointment_type="Checkup"
        )
        assert result1["success"] is True

        # Book second appointment for same patient
        result2 = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name=test_patient.name,
            patient_phone=test_patient.phone,
            date="2026-02-18",
            time="14:00",
            appointment_type="Follow-up"
        )
        assert result2["success"] is True

        # Verify both appointments exist for this patient
        appointments = db_session.query(database.Appointment).filter(
            database.Appointment.patient_id == test_patient.id
        ).all()
        assert len(appointments) == 2

    def test_book_appointment_creates_correct_confirmation(self, db_session: Session, test_doctor_with_oauth):
        """Agent books appointment - confirmation number is properly formatted"""
        result = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name="Test Patient",
            patient_phone="+15551234567",
            date="2026-02-20",
            time="11:00",
            appointment_type="Checkup"
        )

        assert result["success"] is True
        # Confirmation format: CP-YYYYMMDD-ABC
        assert result["confirmation_number"].startswith("CP-")
        assert "20260220" in result["confirmation_number"]


# ============================================================================
# CANCEL APPOINTMENT TESTS
# ============================================================================

class TestAgentCancelAppointment:
    """Test appointment cancellation as used by ElevenLabs agent"""

    def test_cancel_appointment_success(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent cancels existing appointment"""
        # Create appointment
        appointment = database.Appointment(
            id="appt_cancel_test",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-20",
            time="15:00",
            type="Checkup",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()

        # Cancel it
        result = calendar_service.cancel_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            appointment_id="appt_cancel_test"
        )

        assert result["success"] is True
        assert "cancelled" in result["message"].lower()

        # Verify status changed
        updated = db_session.query(database.Appointment).filter(
            database.Appointment.id == "appt_cancel_test"
        ).first()
        assert updated.status == "cancelled"

    def test_cancel_appointment_not_found(self, db_session: Session, test_doctor_with_oauth):
        """Agent tries to cancel non-existent appointment - should fail"""
        result = calendar_service.cancel_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            appointment_id="appt_does_not_exist"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_cancel_updates_timestamp(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent cancels appointment - updated_at timestamp is set"""
        # Create appointment
        created_at = datetime.utcnow()
        appointment = database.Appointment(
            id="appt_timestamp_test",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-21",
            time="13:00",
            type="Checkup",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()
        original_updated_at = appointment.updated_at

        # Wait slightly and cancel
        import time
        time.sleep(0.1)
        calendar_service.cancel_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            appointment_id="appt_timestamp_test"
        )

        # Verify updated_at was changed
        updated = db_session.query(database.Appointment).filter(
            database.Appointment.id == "appt_timestamp_test"
        ).first()
        assert updated.updated_at > original_updated_at


# ============================================================================
# APPOINTMENT RETRIEVAL TESTS
# ============================================================================

class TestAgentGetUpcomingAppointments:
    """Test retrieving appointments as used by ElevenLabs agent"""

    def test_get_upcoming_appointments_returns_only_scheduled(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent retrieves appointments - only returns scheduled/confirmed, not cancelled"""
        # Create multiple appointments with different statuses
        db_session.add(database.Appointment(
            id="appt_scheduled",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-20",
            time="10:00",
            status="scheduled"
        ))
        db_session.add(database.Appointment(
            id="appt_cancelled",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-21",
            time="10:00",
            status="cancelled"
        ))
        db_session.add(database.Appointment(
            id="appt_confirmed",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-22",
            time="10:00",
            status="confirmed"
        ))
        db_session.commit()

        result = calendar_service.get_upcoming_appointments(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            days_ahead=30
        )

        assert len(result) == 2  # Only scheduled and confirmed
        appt_ids = [a["id"] for a in result]
        assert "appt_scheduled" in appt_ids
        assert "appt_confirmed" in appt_ids
        assert "appt_cancelled" not in appt_ids

    def test_get_upcoming_appointments_empty_for_new_patient(self, db_session: Session, test_doctor_with_oauth):
        """Agent retrieves appointments for patient with none - returns empty"""
        # Create new patient with no appointments
        patient = database.Patient(
            id="pat_empty",
            doctor_id=test_doctor_with_oauth.id,
            name="Empty Patient",
            phone="+19999999999"
        )
        db_session.add(patient)
        db_session.commit()

        result = calendar_service.get_upcoming_appointments(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            days_ahead=30
        )

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_upcoming_appointments_respects_date_range(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Agent retrieves appointments - respects days_ahead parameter"""
        # Create appointments in near future and far future
        db_session.add(database.Appointment(
            id="appt_near",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-17",  # Within 30 days
            time="10:00",
            status="scheduled"
        ))
        db_session.add(database.Appointment(
            id="appt_far",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-12-31",  # Far future
            time="10:00",
            status="scheduled"
        ))
        db_session.commit()

        # Get only next 30 days
        result_30 = calendar_service.get_upcoming_appointments(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            days_ahead=30
        )

        assert len(result_30) == 1
        assert result_30[0]["id"] == "appt_near"


# ============================================================================
# EDGE CASE AND ERROR TESTS
# ============================================================================

class TestAgentEdgeCases:
    """Test edge cases and error conditions"""

    def test_book_appointment_with_empty_patient_name(self, db_session: Session, test_doctor_with_oauth):
        """Agent books appointment with empty patient name - should this work or fail?"""
        # This tests expected behavior - currently allows it
        result = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name="",  # Empty name
            patient_phone="+15559999999",
            date="2026-02-17",
            time="10:00"
        )

        # Currently should succeed (no validation)
        assert result["success"] is True

    def test_book_appointment_with_invalid_date_format(self, db_session: Session, test_doctor_with_oauth):
        """Agent books appointment with invalid date format - should gracefully handle"""
        result = calendar_service.book_appointment(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            patient_name="Test",
            patient_phone="+15559999999",
            date="invalid-date",  # Invalid format
            time="10:00"
        )

        # Should either fail or be handled gracefully
        # This test documents expected behavior
        assert isinstance(result, dict)

    def test_cancel_appointment_same_patient_different_doctor(self, db_session: Session, test_doctor_with_oauth, test_patient):
        """Verify appointment belongs to correct doctor before cancelling"""
        # Create second doctor
        doctor2 = database.User(
            id="doctor2_test",
            email="doctor2@test.com",
            name="Dr. Two",
            google_oauth_token=json.dumps({"access_token": "token2"})
        )
        db_session.add(doctor2)

        # Create appointment for doctor1
        appointment = database.Appointment(
            id="appt_doctor_test",
            doctor_id=test_doctor_with_oauth.id,
            patient_id=test_patient.id,
            date="2026-02-20",
            time="10:00",
            status="scheduled"
        )
        db_session.add(appointment)
        db_session.commit()

        # Try to cancel as doctor2 (different doctor)
        result = calendar_service.cancel_appointment(
            user_id=doctor2.id,  # Wrong doctor
            db=db_session,
            appointment_id="appt_doctor_test"
        )

        # Should fail because appointment doesn't belong to this doctor
        assert result["success"] is False

    def test_availability_check_multiple_times_same_date(self, db_session: Session, test_doctor_with_oauth):
        """Agent checks availability multiple times for same date - should be consistent"""
        result1 = calendar_service.check_availability(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            date="2026-02-17"
        )

        result2 = calendar_service.check_availability(
            user_id=test_doctor_with_oauth.id,
            db=db_session,
            date="2026-02-17"
        )

        assert result1["success"] == result2["success"]
        assert len(result1["available_slots"]) == len(result2["available_slots"])
        # Slots should be identical
        for i, slot in enumerate(result1["available_slots"]):
            assert slot == result2["available_slots"][i]
