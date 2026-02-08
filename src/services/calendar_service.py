"""
Calendar business logic service.
Handles appointment scheduling, availability, and related operations.
"""

from datetime import datetime, timedelta, time
from typing import List, Optional, Tuple
import pytz

from src.config import appointment_config
from src.services.google_calendar import google_calendar_client
from src.api.schemas.calendar import (
    TimeSlot, Patient, Appointment, AppointmentStatus, AppointmentType
)


class CalendarService:
    """Business logic for calendar operations."""
    
    def __init__(self):
        self.tz = pytz.timezone(appointment_config.timezone)
        self.duration = appointment_config.duration_minutes
        self.buffer = appointment_config.buffer_minutes
    
    # ============== Date Parsing ==============
    
    def parse_date(self, date_string: str) -> datetime:
        """
        Parse date from various formats including natural language.
        
        Supports: 'today', 'tomorrow', 'next tuesday', 'YYYY-MM-DD', 'MM/DD/YYYY'
        """
        date_string = date_string.lower().strip()
        today = datetime.now(self.tz).date()
        
        # Natural language
        if date_string == "today":
            return self.tz.localize(datetime(today.year, today.month, today.day))
        
        if date_string == "tomorrow":
            tomorrow = today + timedelta(days=1)
            return self.tz.localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day))
        
        if date_string.startswith("next "):
            day_name = date_string.replace("next ", "")
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            if day_name in days:
                target_day = days.index(day_name)
                current_day = today.weekday()
                days_ahead = target_day - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return self.tz.localize(datetime(target_date.year, target_date.month, target_date.day))
        
        # Standard formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d", "%b %d", "%B %d, %Y"]:
            try:
                parsed = datetime.strptime(date_string, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=today.year)
                return self.tz.localize(datetime(parsed.year, parsed.month, parsed.day))
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_string}")
    
    # ============== Availability ==============
    
    def check_availability(
        self, 
        date: str, 
        duration_minutes: Optional[int] = None
    ) -> Tuple[str, str, List[TimeSlot], str]:
        """
        Check available slots for a single date.
        
        Returns:
            Tuple of (date_str, formatted_date, slots, message)
        """
        duration = duration_minutes or self.duration
        
        # Parse date
        try:
            parsed_date = self.parse_date(date)
        except ValueError as e:
            return date, "", [], str(e)
        
        date_str = parsed_date.strftime("%Y-%m-%d")
        formatted_date = parsed_date.strftime("%A, %B %d, %Y")
        
        # Check if in past
        if parsed_date.date() < datetime.now(self.tz).date():
            return date_str, formatted_date, [], "Cannot check availability for past dates."
        
        # Check if day is available
        if parsed_date.weekday() not in appointment_config.available_days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            available_day_names = [day_names[i] for i in appointment_config.available_days]
            return (
                date_str, 
                formatted_date, 
                [], 
                f"Office is closed on {day_names[parsed_date.weekday()]}. Available: {', '.join(available_day_names)}"
            )
        
        # Generate all possible slots
        all_slots = self._generate_time_slots(parsed_date, duration)
        
        # Get busy periods
        day_start = self.tz.localize(datetime(parsed_date.year, parsed_date.month, parsed_date.day, 0, 0, 0))
        day_end = day_start + timedelta(days=1)
        busy_periods = google_calendar_client.get_busy_periods(day_start, day_end)
        
        # Filter available slots
        available_slots = self._filter_available_slots(all_slots, busy_periods)
        
        # Filter past slots (for today)
        available_slots = self._filter_past_slots(available_slots)
        
        # Build message
        if not available_slots:
            message = f"No available appointments on {formatted_date}."
        else:
            times = [slot.formatted_time for slot in available_slots[:5]]
            message = f"Available on {formatted_date}: {', '.join(times)}"
            if len(available_slots) > 5:
                message += f" and {len(available_slots) - 5} more."
        
        return date_str, formatted_date, available_slots, message
    
    def check_availability_range(
        self,
        dates: List[str],
        duration_minutes: Optional[int] = None
    ) -> List[Tuple[str, str, List[TimeSlot], str]]:
        """
        Check availability across multiple dates.
        
        Returns:
            List of (date_str, formatted_date, slots, message) for each date
        """
        results = []
        for date in dates:
            result = self.check_availability(date, duration_minutes)
            results.append(result)
        return results
    
    def is_slot_available(self, appointment_datetime: datetime) -> bool:
        """Check if a specific datetime slot is available."""
        if appointment_datetime.tzinfo is None:
            appointment_datetime = self.tz.localize(appointment_datetime)
        
        date_str = appointment_datetime.strftime("%Y-%m-%d")
        _, _, slots, _ = self.check_availability(date_str)
        
        # Compare by hour and minute only (avoid timezone comparison issues)
        target_time = (appointment_datetime.hour, appointment_datetime.minute)
        target_date = appointment_datetime.date()
        
        for slot in slots:
            slot_time = (slot.start.hour, slot.start.minute)
            slot_date = slot.start.date()
            if slot_time == target_time and slot_date == target_date:
                return True
        return False
    
    def _generate_time_slots(self, date: datetime, duration: int) -> List[TimeSlot]:
        """Generate all possible time slots for a date."""
        slots = []
        
        # Create naive datetime first, then localize properly
        start_time = self.tz.localize(datetime(
            date.year, date.month, date.day,
            appointment_config.available_start_hour,
            appointment_config.available_start_minute,
            0
        ))
        end_time = self.tz.localize(datetime(
            date.year, date.month, date.day,
            appointment_config.available_end_hour,
            appointment_config.available_end_minute,
            0
        ))
        
        current = start_time
        slot_duration = timedelta(minutes=duration)
        buffer = timedelta(minutes=self.buffer)
        
        while current + slot_duration <= end_time:
            slots.append(TimeSlot(
                start=current,
                end=current + slot_duration,
                formatted_time=current.strftime("%-I:%M %p"),
                formatted_date=current.strftime("%A, %B %d")
            ))
            current += slot_duration + buffer
        
        return slots
    
    def _filter_available_slots(
        self, 
        slots: List[TimeSlot], 
        busy_periods: List[dict]
    ) -> List[TimeSlot]:
        """Remove slots that overlap with busy periods."""
        available = []
        
        for slot in slots:
            is_available = True
            
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                
                busy_start = busy_start.astimezone(self.tz)
                busy_end = busy_end.astimezone(self.tz)
                
                # Check overlap
                if not (slot.end <= busy_start or slot.start >= busy_end):
                    is_available = False
                    break
            
            if is_available:
                available.append(slot)
        
        return available
    
    def _filter_past_slots(self, slots: List[TimeSlot]) -> List[TimeSlot]:
        """Remove slots in the past."""
        now = datetime.now(self.tz)
        return [slot for slot in slots if slot.start > now]
    
    # ============== Appointments ==============
    
    def create_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        appointment_datetime: datetime,
        patient_email: Optional[str] = None,
        appointment_type: AppointmentType = AppointmentType.CHECKUP,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str], Optional[Appointment]]:
        """
        Book a new appointment.
        
        Returns:
            Tuple of (success, message, confirmation_id, appointment)
        """
        # Ensure timezone
        if appointment_datetime.tzinfo is None:
            appointment_datetime = self.tz.localize(appointment_datetime)
        
        # Check availability
        if not self.is_slot_available(appointment_datetime):
            return (
                False,
                f"The slot at {appointment_datetime.strftime('%-I:%M %p')} is not available.",
                None,
                None
            )
        
        # Create event
        end_time = appointment_datetime + timedelta(minutes=self.duration)
        
        description = self._build_event_description(
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            appointment_type=appointment_type,
            status=AppointmentStatus.SCHEDULED,
            reminder_sent=False,
            notes=notes
        )
        
        try:
            event = google_calendar_client.create_event(
                summary=f"Appointment: {patient_name}",
                start=appointment_datetime,
                end=end_time,
                description=description
            )
            
            appointment = self._event_to_appointment(event)
            
            return (
                True,
                f"Appointment booked for {appointment.formatted_date} at {appointment.formatted_time}.",
                event["id"],
                appointment
            )
        except Exception as e:
            return False, f"Failed to book appointment: {str(e)}", None, None
    
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        event = google_calendar_client.get_event(appointment_id)
        if not event:
            return None
        return self._event_to_appointment(event)
    
    def reschedule_appointment(
        self,
        appointment_id: str,
        new_datetime: datetime
    ) -> Tuple[bool, str, Optional[Appointment]]:
        """
        Reschedule an appointment.
        
        Returns:
            Tuple of (success, message, appointment)
        """
        if new_datetime.tzinfo is None:
            new_datetime = self.tz.localize(new_datetime)
        
        # Check new slot availability
        if not self.is_slot_available(new_datetime):
            return (
                False,
                f"The new slot at {new_datetime.strftime('%-I:%M %p')} is not available.",
                None
            )
        
        # Get existing event
        event = google_calendar_client.get_event(appointment_id)
        if not event:
            return False, "Appointment not found.", None
        
        # Update times
        new_end = new_datetime + timedelta(minutes=self.duration)
        
        # Reset reminder status
        description = event.get("description", "")
        description = description.replace("Reminder Sent: true", "Reminder Sent: false")
        
        updated_event = google_calendar_client.update_event(
            appointment_id,
            {
                "start": new_datetime,
                "end": new_end,
                "description": description
            }
        )
        
        if not updated_event:
            return False, "Failed to reschedule appointment.", None
        
        appointment = self._event_to_appointment(updated_event)
        return (
            True,
            f"Appointment rescheduled to {appointment.formatted_date} at {appointment.formatted_time}.",
            appointment
        )
    
    def cancel_appointment(self, appointment_id: str) -> Tuple[bool, str]:
        """
        Cancel an appointment.
        
        Returns:
            Tuple of (success, message)
        """
        event = google_calendar_client.get_event(appointment_id)
        if not event:
            return False, "Appointment not found."
        
        # Update status instead of deleting
        description = event.get("description", "")
        description = self._update_description_field(description, "Status", "cancelled")
        
        summary = event.get("summary", "").replace("Appointment:", "CANCELLED:")
        
        updated = google_calendar_client.update_event(
            appointment_id,
            {"description": description, "summary": summary}
        )
        
        if updated:
            return True, "Appointment cancelled successfully."
        return False, "Failed to cancel appointment."
    
    def mark_reminder_sent(self, appointment_id: str) -> Tuple[bool, str]:
        """Mark that reminder was sent."""
        event = google_calendar_client.get_event(appointment_id)
        if not event:
            return False, "Appointment not found."
        
        description = event.get("description", "")
        description = self._update_description_field(description, "Reminder Sent", "true")
        
        updated = google_calendar_client.update_event(
            appointment_id,
            {"description": description}
        )
        
        if updated:
            return True, "Reminder marked as sent."
        return False, "Failed to update appointment."
    
    def mark_no_show(self, appointment_id: str) -> Tuple[bool, str]:
        """Mark appointment as no-show."""
        event = google_calendar_client.get_event(appointment_id)
        if not event:
            return False, "Appointment not found."
        
        description = event.get("description", "")
        description = self._update_description_field(description, "Status", "no_show")
        
        summary = event.get("summary", "").replace("Appointment:", "NO SHOW:")
        
        updated = google_calendar_client.update_event(
            appointment_id,
            {"description": description, "summary": summary}
        )
        
        if updated:
            return True, "Appointment marked as no-show."
        return False, "Failed to update appointment."
    
    def get_upcoming_appointments(
        self, 
        hours_ahead: Optional[int] = None
    ) -> List[Appointment]:
        """Get upcoming appointments, optionally within N hours."""
        now = datetime.now(self.tz)
        
        if hours_ahead:
            time_max = now + timedelta(hours=hours_ahead)
            events = google_calendar_client.get_events_in_range(now, time_max)
        else:
            events = google_calendar_client.list_events(time_min=now)
        
        appointments = []
        for event in events:
            if event.get("summary", "").startswith("Appointment:"):
                appointments.append(self._event_to_appointment(event))
        
        return appointments
    
    def get_all_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> List[dict]:
        """Get raw calendar events for doctor dashboard."""
        if time_min and time_min.tzinfo is None:
            time_min = self.tz.localize(time_min)
        if time_max and time_max.tzinfo is None:
            time_max = self.tz.localize(time_max)
        
        return google_calendar_client.list_events(
            time_min=time_min,
            time_max=time_max
        )
    
    # ============== Helpers ==============
    
    def _build_event_description(
        self,
        patient_name: str,
        patient_phone: str,
        patient_email: Optional[str],
        appointment_type: AppointmentType,
        status: AppointmentStatus,
        reminder_sent: bool,
        notes: Optional[str]
    ) -> str:
        """Build event description with metadata."""
        return f"""Patient: {patient_name}
Phone: {patient_phone}
Email: {patient_email or 'N/A'}
Type: {appointment_type.value}
Status: {status.value}
Reminder Sent: {str(reminder_sent).lower()}
Notes: {notes or 'None'}"""
    
    def _update_description_field(
        self, 
        description: str, 
        field: str, 
        value: str
    ) -> str:
        """Update a specific field in description."""
        lines = description.split("\n")
        updated_lines = []
        field_found = False
        
        for line in lines:
            if line.startswith(f"{field}:"):
                updated_lines.append(f"{field}: {value}")
                field_found = True
            else:
                updated_lines.append(line)
        
        if not field_found:
            updated_lines.append(f"{field}: {value}")
        
        return "\n".join(updated_lines)
    
    def _parse_description(self, description: str) -> dict:
        """Parse event description into dict."""
        parsed = {}
        for line in description.split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                parsed[key.lower().replace(" ", "_")] = value
        return parsed
    
    def _event_to_appointment(self, event: dict) -> Appointment:
        """Convert Google Calendar event to Appointment model."""
        description = event.get("description", "")
        parsed = self._parse_description(description)
        
        start_str = event["start"].get("dateTime", event["start"].get("date"))
        end_str = event["end"].get("dateTime", event["end"].get("date"))
        
        start_time = datetime.fromisoformat(start_str)
        end_time = datetime.fromisoformat(end_str)
        
        # Parse status
        status_str = parsed.get("status", "scheduled")
        try:
            status = AppointmentStatus(status_str)
        except ValueError:
            status = AppointmentStatus.SCHEDULED
        
        # Parse type
        type_str = parsed.get("type", "checkup")
        try:
            apt_type = AppointmentType(type_str)
        except ValueError:
            apt_type = AppointmentType.CHECKUP
        
        return Appointment(
            id=event["id"],
            patient=Patient(
                name=parsed.get("patient", "Unknown"),
                phone=parsed.get("phone", ""),
                email=parsed.get("email") if parsed.get("email") != "N/A" else None,
                notes=parsed.get("notes") if parsed.get("notes") != "None" else None
            ),
            start_time=start_time,
            end_time=end_time,
            formatted_time=start_time.strftime("%-I:%M %p"),
            formatted_date=start_time.strftime("%A, %B %d, %Y"),
            appointment_type=apt_type,
            status=status,
            reminder_sent=parsed.get("reminder_sent", "false").lower() == "true"
        )


# Global service instance
calendar_service = CalendarService()