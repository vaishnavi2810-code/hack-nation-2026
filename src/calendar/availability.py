"""
Functions to check appointment availability using Google Calendar Free/Busy API.
"""

from datetime import datetime, timedelta, time
from typing import List, Optional
import pytz

from src.config import calendar_config
from src.calendar.client import get_calendar_service
from src.calendar.models import TimeSlot, AvailabilityResponse


def parse_date(date_string: str) -> datetime:
    """
    Parse date from various formats including natural language.
    
    Supports:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - "today", "tomorrow"
    - "next tuesday", "next week"
    """
    date_string = date_string.lower().strip()
    tz = pytz.timezone(calendar_config.timezone)
    today = datetime.now(tz).date()
    
    # Handle natural language
    if date_string == "today":
        return datetime.combine(today, time.min).replace(tzinfo=tz)
    elif date_string == "tomorrow":
        return datetime.combine(today + timedelta(days=1), time.min).replace(tzinfo=tz)
    elif date_string.startswith("next "):
        day_name = date_string.replace("next ", "")
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if day_name in days:
            target_day = days.index(day_name)
            current_day = today.weekday()
            days_ahead = target_day - current_day
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return datetime.combine(target_date, time.min).replace(tzinfo=tz)
    
    # Try standard formats
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d", "%b %d"]:
        try:
            parsed = datetime.strptime(date_string, fmt)
            if parsed.year == 1900:  # No year in format
                parsed = parsed.replace(year=today.year)
            return tz.localize(parsed)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse date: {date_string}")


def get_busy_periods(date: datetime) -> List[dict]:
    """
    Query Google Calendar Free/Busy API for a specific date.
    Returns list of busy time periods.
    """
    service = get_calendar_service()
    tz = pytz.timezone(calendar_config.timezone)
    
    # Set time boundaries for the day
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    body = {
        "timeMin": day_start.isoformat(),
        "timeMax": day_end.isoformat(),
        "timeZone": calendar_config.timezone,
        "items": [{"id": calendar_config.calendar_id}]
    }
    
    result = service.freebusy().query(body=body).execute()
    calendar_data = result.get("calendars", {}).get(calendar_config.calendar_id, {})
    
    return calendar_data.get("busy", [])


def generate_time_slots(date: datetime, duration_minutes: int) -> List[TimeSlot]:
    """
    Generate all possible time slots for a given date based on config.
    """
    tz = pytz.timezone(calendar_config.timezone)
    slots = []
    
    # Check if this day is available
    if date.weekday() not in calendar_config.available_days:
        return slots
    
    # Create start and end times for this date
    start_time = date.replace(
        hour=calendar_config.available_start_hour,
        minute=calendar_config.available_start_minute,
        second=0,
        microsecond=0
    )
    end_time = date.replace(
        hour=calendar_config.available_end_hour,
        minute=calendar_config.available_end_minute,
        second=0,
        microsecond=0
    )
    
    # Generate slots
    current = start_time
    slot_duration = timedelta(minutes=duration_minutes)
    buffer = timedelta(minutes=calendar_config.buffer_between_appointments_minutes)
    
    while current + slot_duration <= end_time:
        slots.append(TimeSlot(start=current, end=current + slot_duration))
        current += slot_duration + buffer
    
    return slots


def filter_available_slots(
    all_slots: List[TimeSlot], 
    busy_periods: List[dict]
) -> List[TimeSlot]:
    """
    Remove slots that overlap with busy periods.
    """
    tz = pytz.timezone(calendar_config.timezone)
    available = []
    
    for slot in all_slots:
        is_available = True
        
        for busy in busy_periods:
            busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
            
            # Convert to same timezone for comparison
            busy_start = busy_start.astimezone(tz)
            busy_end = busy_end.astimezone(tz)
            
            # Check for overlap
            if not (slot.end <= busy_start or slot.start >= busy_end):
                is_available = False
                break
        
        if is_available:
            available.append(slot)
    
    return available


def filter_past_slots(slots: List[TimeSlot]) -> List[TimeSlot]:
    """Remove slots that are in the past."""
    tz = pytz.timezone(calendar_config.timezone)
    now = datetime.now(tz)
    return [slot for slot in slots if slot.start > now]


def check_availability(
    date: str,
    duration_minutes: Optional[int] = None
) -> AvailabilityResponse:
    """
    Main function to check available appointment slots for a date.
    
    Args:
        date: Date string (YYYY-MM-DD or natural language like "tomorrow")
        duration_minutes: Optional override for appointment duration
    
    Returns:
        AvailabilityResponse with available time slots
    """
    # Use config default if not specified
    if duration_minutes is None:
        duration_minutes = calendar_config.appointment_duration_minutes
    
    # Parse the date
    try:
        parsed_date = parse_date(date)
    except ValueError as e:
        return AvailabilityResponse(
            date=date,
            available_slots=[],
            message=f"Could not understand the date: {date}. Please try YYYY-MM-DD format."
        )
    
    # Check if date is in the past
    tz = pytz.timezone(calendar_config.timezone)
    if parsed_date.date() < datetime.now(tz).date():
        return AvailabilityResponse(
            date=parsed_date.strftime("%Y-%m-%d"),
            available_slots=[],
            message="Cannot book appointments in the past."
        )
    
    # Check if day is available
    if parsed_date.weekday() not in calendar_config.available_days:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        available_day_names = [day_names[i] for i in calendar_config.available_days]
        return AvailabilityResponse(
            date=parsed_date.strftime("%Y-%m-%d"),
            available_slots=[],
            message=f"The office is closed on {day_names[parsed_date.weekday()]}. "
                    f"Available days are: {', '.join(available_day_names)}."
        )
    
    # Generate all possible slots
    all_slots = generate_time_slots(parsed_date, duration_minutes)
    
    # Get busy periods from Google Calendar
    busy_periods = get_busy_periods(parsed_date)
    
    # Filter out busy slots
    available_slots = filter_available_slots(all_slots, busy_periods)
    
    # Filter out past slots (for today)
    available_slots = filter_past_slots(available_slots)
    
    # Build response
    if not available_slots:
        message = f"No available appointments on {parsed_date.strftime('%A, %B %d')}."
    else:
        times = [slot.formatted_time for slot in available_slots[:5]]  # Show max 5
        message = f"Available times on {parsed_date.strftime('%A, %B %d')}: {', '.join(times)}"
        if len(available_slots) > 5:
            message += f" and {len(available_slots) - 5} more."
    
    return AvailabilityResponse(
        date=parsed_date.strftime("%Y-%m-%d"),
        available_slots=available_slots,
        message=message
    )


def is_slot_available(appointment_datetime: datetime) -> bool:
    """
    Check if a specific datetime slot is available.
    Used for validation before booking.
    """
    tz = pytz.timezone(calendar_config.timezone)
    
    # Ensure datetime is timezone-aware
    if appointment_datetime.tzinfo is None:
        appointment_datetime = tz.localize(appointment_datetime)
    
    date_str = appointment_datetime.strftime("%Y-%m-%d")
    response = check_availability(date_str)
    
    for slot in response.available_slots:
        if slot.start == appointment_datetime:
            return True
    
    return False