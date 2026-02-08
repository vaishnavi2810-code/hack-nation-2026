"""
Pydantic models for CallPilot calendar operations.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    """Status of an appointment."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class AppointmentType(str, Enum):
    """Type of medical appointment."""
    CHECKUP = "checkup"
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    URGENT = "urgent"
    OTHER = "other"


class TimeSlot(BaseModel):
    """Represents an available time slot."""
    start: datetime
    end: datetime
    
    @property
    def formatted_time(self) -> str:
        """Return human-readable time like '2:00 PM'."""
        return self.start.strftime("%-I:%M %p")
    
    @property
    def formatted_date(self) -> str:
        """Return human-readable date like 'Tuesday, February 11'."""
        return self.start.strftime("%A, %B %d")


class Patient(BaseModel):
    """Patient information stored in calendar event."""
    name: str = Field(..., description="Patient full name")
    phone: str = Field(..., description="Patient phone number")
    email: Optional[str] = Field(default=None, description="Patient email")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class Appointment(BaseModel):
    """Represents a booked appointment."""
    id: Optional[str] = Field(default=None, description="Google Calendar event ID")
    patient: Patient
    start_time: datetime
    end_time: datetime
    appointment_type: AppointmentType = AppointmentType.CHECKUP
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reminder_sent: bool = False
    created_at: Optional[datetime] = None
    
    @property
    def formatted_time(self) -> str:
        return self.start_time.strftime("%-I:%M %p")
    
    @property
    def formatted_date(self) -> str:
        return self.start_time.strftime("%A, %B %d, %Y")
    
    def to_calendar_description(self) -> str:
        """Convert to Google Calendar event description format."""
        return f"""Patient: {self.patient.name}
Phone: {self.patient.phone}
Email: {self.patient.email or 'N/A'}
Type: {self.appointment_type.value}
Status: {self.status.value}
Reminder Sent: {str(self.reminder_sent).lower()}
Notes: {self.patient.notes or 'None'}"""
    
    @classmethod
    def from_calendar_event(cls, event: dict) -> "Appointment":
        """Parse a Google Calendar event into an Appointment."""
        description = event.get("description", "")
        
        # Parse description fields
        lines = description.split("\n")
        parsed = {}
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                parsed[key.lower().replace(" ", "_")] = value
        
        patient = Patient(
            name=parsed.get("patient", "Unknown"),
            phone=parsed.get("phone", ""),
            email=parsed.get("email") if parsed.get("email") != "N/A" else None,
            notes=parsed.get("notes") if parsed.get("notes") != "None" else None
        )
        
        return cls(
            id=event.get("id"),
            patient=patient,
            start_time=datetime.fromisoformat(
                event["start"].get("dateTime", event["start"].get("date"))
            ),
            end_time=datetime.fromisoformat(
                event["end"].get("dateTime", event["end"].get("date"))
            ),
            appointment_type=AppointmentType(parsed.get("type", "checkup")),
            status=AppointmentStatus(parsed.get("status", "scheduled")),
            reminder_sent=parsed.get("reminder_sent", "false").lower() == "true",
            created_at=datetime.fromisoformat(event["created"]) if "created" in event else None
        )


class AvailabilityRequest(BaseModel):
    """Request to check availability."""
    date: str = Field(..., description="Date to check (YYYY-MM-DD or natural language)")
    duration_minutes: Optional[int] = Field(default=None, description="Override default duration")


class AvailabilityResponse(BaseModel):
    """Response with available time slots."""
    date: str
    available_slots: List[TimeSlot]
    message: str
    
    @property
    def formatted_slots(self) -> List[str]:
        """Return list of formatted time strings."""
        return [slot.formatted_time for slot in self.available_slots]


class BookingRequest(BaseModel):
    """Request to book an appointment."""
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None
    appointment_datetime: datetime
    appointment_type: AppointmentType = AppointmentType.CHECKUP
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Response after booking."""
    success: bool
    appointment: Optional[Appointment] = None
    message: str
    confirmation_id: Optional[str] = None