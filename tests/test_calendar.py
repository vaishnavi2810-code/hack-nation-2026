"""
Tests for CallPilot calendar functions.

Run with: pytest tests/test_calendar.py -v
"""

import pytest
from datetime import datetime, timedelta
import pytz

from src.calendar.availability import parse_date, generate_time_slots, check_availability
from src.calendar.models import TimeSlot, AppointmentType
from src.config import calendar_config


class TestParseDate:
    """Test date parsing functionality."""
    
    def test_parse_iso_format(self):
        result = parse_date("2026-02-15")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 15
    
    def test_parse_us_format(self):
        result = parse_date("02/15/2026")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 15
    
    def test_parse_today(self):
        tz = pytz.timezone(calendar_config.timezone)
        result = parse_date("today")
        today = datetime.now(tz).date()
        assert result.date() == today
    
    def test_parse_tomorrow(self):
        tz = pytz.timezone(calendar_config.timezone)
        result = parse_date("tomorrow")
        tomorrow = datetime.now(tz).date() + timedelta(days=1)
        assert result.date() == tomorrow
    
    def test_parse_next_weekday(self):
        result = parse_date("next tuesday")
        assert result.weekday() == 1  # Tuesday
    
    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError):
            parse_date("invalid date format xyz")


class TestGenerateTimeSlots:
    """Test time slot generation."""
    
    def test_generates_slots_for_available_day(self):
        tz = pytz.timezone(calendar_config.timezone)
        # Find next Monday (available day)
        today = datetime.now(tz)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        monday = today + timedelta(days=days_until_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        slots = generate_time_slots(monday, duration_minutes=30)
        
        assert len(slots) > 0
        assert all(isinstance(slot, TimeSlot) for slot in slots)
    
    def test_no_slots_for_weekend(self):
        tz = pytz.timezone(calendar_config.timezone)
        # Find next Saturday
        today = datetime.now(tz)
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = today + timedelta(days=days_until_saturday)
        saturday = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Only test if Saturday is not in available days
        if 5 not in calendar_config.available_days:
            slots = generate_time_slots(saturday, duration_minutes=30)
            assert len(slots) == 0
    
    def test_slot_duration_is_correct(self):
        tz = pytz.timezone(calendar_config.timezone)
        today = datetime.now(tz)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        monday = today + timedelta(days=days_until_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        slots = generate_time_slots(monday, duration_minutes=30)
        
        if slots:
            first_slot = slots[0]
            duration = (first_slot.end - first_slot.start).seconds / 60
            assert duration == 30


class TestTimeSlotModel:
    """Test TimeSlot model methods."""
    
    def test_formatted_time(self):
        tz = pytz.timezone(calendar_config.timezone)
        slot = TimeSlot(
            start=datetime(2026, 2, 15, 14, 0, tzinfo=tz),
            end=datetime(2026, 2, 15, 14, 30, tzinfo=tz)
        )
        assert "2:00 PM" in slot.formatted_time or "2:00PM" in slot.formatted_time
    
    def test_formatted_date(self):
        tz = pytz.timezone(calendar_config.timezone)
        slot = TimeSlot(
            start=datetime(2026, 2, 15, 14, 0, tzinfo=tz),
            end=datetime(2026, 2, 15, 14, 30, tzinfo=tz)
        )
        assert "February" in slot.formatted_date
        assert "15" in slot.formatted_date


class TestCheckAvailability:
    """
    Integration tests for availability checking.
    Note: These require Google Calendar API credentials.
    """
    
    @pytest.mark.skip(reason="Requires Google Calendar API credentials")
    def test_check_availability_returns_response(self):
        response = check_availability("tomorrow")
        assert response is not None
        assert hasattr(response, "available_slots")
        assert hasattr(response, "message")
    
    @pytest.mark.skip(reason="Requires Google Calendar API credentials")
    def test_past_date_returns_empty(self):
        response = check_availability("2020-01-01")
        assert len(response.available_slots) == 0
        assert "past" in response.message.lower()


# Run with: pytest tests/test_calendar.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])