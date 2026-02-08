"""
Direct Google Calendar API interactions.
Low-level functions for calendar operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pytz

from src.config import appointment_config
from src.core.auth import auth_manager


class GoogleCalendarClient:
    """Low-level Google Calendar API client."""
    
    def __init__(self):
        self.timezone = pytz.timezone(appointment_config.timezone)
        self.calendar_id = "primary"
    
    def _get_service(self):
        """Get authenticated calendar service."""
        service = auth_manager.get_calendar_service()
        if not service:
            raise ConnectionError("Not connected to Google Calendar. Please authenticate first.")
        return service
    
    # ============== Free/Busy Queries ==============
    
    def get_busy_periods(self, start: datetime, end: datetime) -> List[Dict[str, str]]:
        """
        Query Google Calendar Free/Busy API.
        
        Args:
            start: Start of time range
            end: End of time range
            
        Returns:
            List of busy periods with 'start' and 'end' keys
        """
        service = self._get_service()
        
        # Ensure timezone awareness
        if start.tzinfo is None:
            start = self.timezone.localize(start)
        if end.tzinfo is None:
            end = self.timezone.localize(end)
        
        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "timeZone": appointment_config.timezone,
            "items": [{"id": self.calendar_id}]
        }
        
        result = service.freebusy().query(body=body).execute()
        calendar_data = result.get("calendars", {}).get(self.calendar_id, {})
        
        return calendar_data.get("busy", [])
    
    # ============== Event CRUD ==============
    
    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str = ""
    ) -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Returns:
            Created event data from Google
        """
        service = self._get_service()
        
        # Ensure timezone awareness
        if start.tzinfo is None:
            start = self.timezone.localize(start)
        if end.tzinfo is None:
            end = self.timezone.localize(end)
        
        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": appointment_config.timezone
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": appointment_config.timezone
            },
            "reminders": {
                "useDefault": False,
                "overrides": []
            }
        }
        
        created_event = service.events().insert(
            calendarId=self.calendar_id,
            body=event
        ).execute()
        
        return created_event
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single event by ID.
        
        Returns:
            Event data or None if not found
        """
        service = self._get_service()
        
        try:
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return event
        except Exception:
            return None
    
    def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing event.
        
        Args:
            event_id: Google Calendar event ID
            updates: Fields to update
            
        Returns:
            Updated event data or None
        """
        service = self._get_service()
        
        try:
            # Get existing event
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Apply updates
            for key, value in updates.items():
                if key in ["start", "end"] and isinstance(value, datetime):
                    if value.tzinfo is None:
                        value = self.timezone.localize(value)
                    event[key] = {
                        "dateTime": value.isoformat(),
                        "timeZone": appointment_config.timezone
                    }
                else:
                    event[key] = value
            
            # Save
            updated_event = service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return updated_event
            
        except Exception:
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event.
        
        Returns:
            True if deleted, False otherwise
        """
        service = self._get_service()
        
        try:
            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception:
            return False
    
    # ============== Event Queries ==============
    
    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List calendar events.
        
        Args:
            time_min: Start of time range (default: now)
            time_max: End of time range (optional)
            max_results: Maximum events to return
            query: Search query string
            
        Returns:
            List of event data
        """
        service = self._get_service()
        
        # Default to now
        if time_min is None:
            time_min = datetime.now(self.timezone)
        elif time_min.tzinfo is None:
            time_min = self.timezone.localize(time_min)
        
        params = {
            "calendarId": self.calendar_id,
            "timeMin": time_min.isoformat(),
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_max:
            if time_max.tzinfo is None:
                time_max = self.timezone.localize(time_max)
            params["timeMax"] = time_max.isoformat()
        
        if query:
            params["q"] = query
        
        result = service.events().list(**params).execute()
        return result.get("items", [])
    
    def search_events(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search events by text query.
        """
        return self.list_events(query=query, max_results=max_results)
    
    def get_events_in_range(
        self, 
        start: datetime, 
        end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get all events within a specific time range.
        """
        return self.list_events(time_min=start, time_max=end, max_results=100)


# Global client instance
google_calendar_client = GoogleCalendarClient()