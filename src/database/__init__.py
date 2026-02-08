"""
Database models and session management.
"""

from src.database.models import (
    engine,
    SessionLocal,
    Base,
    User,
    Patient,
    Appointment,
    Call,
    UserSession,
    init_db,
    get_db,
)

# Type alias for FastAPI dependencies
Session = SessionLocal

__all__ = [
    "engine",
    "SessionLocal",
    "Session",
    "Base",
    "User",
    "Patient",
    "Appointment",
    "Call",
    "UserSession",
    "init_db",
    "get_db",
]
