"""
Database models for CallPilot.

Defines SQLAlchemy models for:
- Users (doctors) with OAuth tokens
- Patients
- Appointments
- Call records
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from src import config

# Create database engine
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# ============================================================================
# USER MODEL (Doctor)
# ============================================================================

class User(Base):
    """Doctor user account with Google OAuth authentication"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)  # user_123
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    timezone = Column(String(50), default=config.DOCTOR_TIMEZONE)

    # OAuth token storage
    google_oauth_token = Column(Text, nullable=True)  # JSON-encoded token from Google
    google_refresh_token = Column(Text, nullable=True)  # Refresh token for token renewal
    google_token_expiry = Column(DateTime, nullable=True)  # When token expires
    google_calendar_id = Column(String(255), nullable=True)  # User's Google Calendar ID

    # Account status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patients = relationship("Patient", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    calls = relationship("Call", back_populates="doctor")

    class Config:
        from_attributes = True


# ============================================================================
# PATIENT MODEL
# ============================================================================

class Patient(Base):
    """Patient record linked to a doctor"""
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True, index=True)  # pat_123
    doctor_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("User", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    calls = relationship("Call", back_populates="patient")

    class Config:
        from_attributes = True


# ============================================================================
# APPOINTMENT MODEL
# ============================================================================

class Appointment(Base):
    """Appointment record linked to patient and doctor"""
    __tablename__ = "appointments"

    id = Column(String(50), primary_key=True, index=True)  # appt_123
    doctor_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    calendar_event_id = Column(String(255), nullable=True)  # Google Calendar event ID

    # Appointment details
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    time = Column(String(5), nullable=False)  # HH:MM
    duration_minutes = Column(Integer, default=config.APPOINTMENT_DURATION_MINUTES)
    type = Column(String(100), default="General Checkup")
    notes = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(50), default="scheduled")  # scheduled, confirmed, completed, cancelled, no_show
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("User", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    class Config:
        from_attributes = True


# ============================================================================
# CALL MODEL
# ============================================================================

class Call(Base):
    """Inbound or outbound call record"""
    __tablename__ = "calls"

    id = Column(String(50), primary_key=True, index=True)  # call_123
    doctor_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=True)
    call_sid = Column(String(100), unique=True, index=True)  # Twilio Call SID

    # Call details
    direction = Column(String(20))  # inbound, outbound
    type = Column(String(50))  # booking, reminder, confirmation, manual
    phone_number = Column(String(20), nullable=False)
    status = Column(String(50))  # initiated, ringing, in-progress, completed, failed

    # Recording and metadata
    duration_seconds = Column(Integer, default=0)
    transcript = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("User", back_populates="calls")
    patient = relationship("Patient", back_populates="calls")

    class Config:
        from_attributes = True


# ============================================================================
# SESSION/AUTHENTICATION MODEL
# ============================================================================

class UserSession(Base):
    """Track active user sessions with JWT tokens"""
    __tablename__ = "user_sessions"

    id = Column(String(100), primary_key=True, index=True)  # Session ID
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)  # JWT access token
    refresh_token = Column(Text, nullable=False)  # JWT refresh token
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (dependency for FastAPI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
