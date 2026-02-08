Great question! Let me design a complete calendar API with all the endpoints and response formats:

  Calendar API Endpoints

  ┌────────────────────────────────────────────────────────────────────┐
  │                    CALENDAR API DESIGN                              │
  └────────────────────────────────────────────────────────────────────┘

  1. Check Calendar Connection Status

  GET /api/calendar/status
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "connected": true,
    "calendar_id": "user@gmail.com",
    "email": "doctor@gmail.com",
    "connected_at": "2026-02-01T10:30:00Z",
    "last_sync": "2026-02-07T14:45:00Z"
  }

  2. Check Availability

  POST /api/calendar/check-availability
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

  Request:
  {
    "date": "2026-02-18"
  }

  Response (200 OK):
  {
    "success": true,
    "date": "2026-02-18",
    "available_slots": [
      {
        "date": "2026-02-18",
        "time": "09:00",
        "duration_minutes": 30
      },
      {
        "date": "2026-02-18",
        "time": "09:30",
        "duration_minutes": 30
      },
      {
        "date": "2026-02-18",
        "time": "10:00",
        "duration_minutes": 30
      }
    ]
  }

  Response (400/401):
  {
    "success": false,
    "date": "2026-02-18",
    "error": "Calendar not connected" or "Invalid date format"
  }

  3. Check Availability for Multiple Dates

  POST /api/calendar/check-availability-range
  Authorization: Bearer {jwt_token}

  Request:
  {
    "start_date": "2026-02-18",
    "end_date": "2026-02-25",
    "duration_minutes": 30
  }

  Response (200 OK):
  {
    "success": true,
    "results": [
      {
        "date": "2026-02-18",
        "available_count": 8,
        "first_available_time": "09:00",
        "available_slots": [...]
      },
      {
        "date": "2026-02-19",
        "available_count": 6,
        "first_available_time": "10:00",
        "available_slots": [...]
      }
    ]
  }

  4. Create Appointment (Book)

  POST /api/calendar/appointments
  Authorization: Bearer {jwt_token}

  Request:
  {
    "patient_id": "pat_abc123",
    "patient_name": "John Doe",
    "patient_phone": "+14155552671",
    "date": "2026-02-18",
    "time": "14:00",
    "appointment_type": "General Checkup",
    "notes": "Patient has hypertension"
  }

  Response (201 Created):
  {
    "success": true,
    "appointment_id": "appt_abc123",
    "calendar_event_id": "calendar_event_xyz789",
    "date": "2026-02-18",
    "time": "14:00",
    "duration_minutes": 30,
    "patient_name": "John Doe",
    "confirmation_number": "CP-20260218-ABC",
    "message": "Appointment confirmed for John Doe on 2026-02-18 at 14:00",
    "sms_sent": true
  }

  Response (400 Bad Request):
  {
    "success": false,
    "error": "Time slot not available",
    "details": "Requested time conflicts with existing event"
  }

  Response (409 Conflict):
  {
    "success": false,
    "error": "Slot already booked",
    "details": "Another appointment was just created for this time"
  }

  5. Get Appointment Details

  GET /api/calendar/appointments/{appointment_id}
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "success": true,
    "appointment": {
      "id": "appt_abc123",
      "calendar_event_id": "calendar_event_xyz789",
      "patient_id": "pat_abc123",
      "patient_name": "John Doe",
      "patient_phone": "+14155552671",
      "date": "2026-02-18",
      "time": "14:00",
      "duration_minutes": 30,
      "type": "General Checkup",
      "notes": "Patient has hypertension",
      "status": "scheduled",
      "reminder_sent": false,
      "reminder_sent_at": null,
      "created_at": "2026-02-07T10:30:00Z",
      "updated_at": "2026-02-07T10:30:00Z"
    }
  }

  Response (404 Not Found):
  {
    "success": false,
    "error": "Appointment not found"
  }

  6. Update Appointment

  PATCH /api/calendar/appointments/{appointment_id}
  Authorization: Bearer {jwt_token}

  Request:
  {
    "date": "2026-02-19",
    "time": "15:00",
    "appointment_type": "Follow-up",
    "notes": "Reschedule due to patient request"
  }

  Response (200 OK):
  {
    "success": true,
    "appointment": {
      "id": "appt_abc123",
      "date": "2026-02-19",
      "time": "15:00",
      "appointment_type": "Follow-up",
      "notes": "Reschedule due to patient request",
      "message": "Appointment rescheduled to 2026-02-19 at 15:00"
    }
  }

  Response (400 Bad Request):
  {
    "success": false,
    "error": "New time slot not available"
  }

  7. Cancel Appointment

  DELETE /api/calendar/appointments/{appointment_id}
  Authorization: Bearer {jwt_token}

  Request (optional):
  {
    "reason": "Patient requested cancellation"
  }

  Response (200 OK):
  {
    "success": true,
    "message": "Appointment cancelled",
    "appointment_id": "appt_abc123",
    "calendar_event_id": "calendar_event_xyz789",
    "cancelled_at": "2026-02-07T14:45:00Z",
    "sms_sent": true
  }

  Response (404 Not Found):
  {
    "success": false,
    "error": "Appointment not found"
  }

  8. List Upcoming Appointments

  GET /api/calendar/appointments?days=30&limit=50
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "success": true,
    "count": 12,
    "appointments": [
      {
        "id": "appt_abc123",
        "patient_name": "John Doe",
        "patient_phone": "+14155552671",
        "date": "2026-02-18",
        "time": "14:00",
        "duration_minutes": 30,
        "type": "General Checkup",
        "status": "scheduled",
        "reminder_sent": false
      },
      {
        "id": "appt_def456",
        "patient_name": "Jane Smith",
        "patient_phone": "+14155552672",
        "date": "2026-02-19",
        "time": "15:00",
        "duration_minutes": 30,
        "type": "Follow-up",
        "status": "scheduled",
        "reminder_sent": true
      }
    ]
  }

  9. Get Calendar Events (Raw)

  GET /api/calendar/events?start_date=2026-02-18&end_date=2026-02-25
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "success": true,
    "events": [
      {
        "id": "calendar_event_xyz789",
        "summary": "Appointment: John Doe",
        "description": "Patient: John Doe\nPhone: +14155552671\nType: General Checkup",
        "start": "2026-02-18T14:00:00Z",
        "end": "2026-02-18T14:30:00Z",
        "location": null,
        "hangout_link": null
      }
    ]
  }

  10. Connect Calendar (OAuth)

  GET /api/calendar/auth-url
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
    "state": "state_token_xyz"
  }

  11. OAuth Callback Handler

  POST /api/calendar/auth-callback
  Authorization: Bearer {jwt_token}

  Request:
  {
    "code": "4/0AX4XfWh...",
    "state": "state_token_xyz"
  }

  Response (200 OK):
  {
    "success": true,
    "message": "Calendar connected successfully",
    "calendar_id": "user@gmail.com",
    "email": "doctor@gmail.com"
  }

  Response (400 Bad Request):
  {
    "success": false,
    "error": "Failed to authenticate with Google",
    "details": "Invalid authorization code"
  }

  12. Disconnect Calendar

  DELETE /api/calendar/disconnect
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "success": true,
    "message": "Calendar disconnected"
  }

  13. Mark Reminder as Sent

  PATCH /api/calendar/appointments/{appointment_id}/remind
  Authorization: Bearer {jwt_token}

  Response (200 OK):
  {
    "success": true,
    "appointment_id": "appt_abc123",
    "reminder_sent": true,
    "reminder_sent_at": "2026-02-18T13:00:00Z"
  }

  ---
  Pydantic Models for Responses

  Add these to src/core/models.py:

  # ============================================================================
  # CALENDAR API MODELS
  # ============================================================================

  class AvailabilitySlot(BaseModel):
      """Available appointment time slot"""
      date: str  # YYYY-MM-DD
      time: str  # HH:MM
      duration_minutes: int


  class AvailabilityRequest(BaseModel):
      """Request to check available slots"""
      date: str  # YYYY-MM-DD


  class AvailabilityRangeRequest(BaseModel):
      """Request to check availability for multiple dates"""
      start_date: str
      end_date: str
      duration_minutes: int = 30


  class AvailabilityResponse(BaseModel):
      """Response with available appointment slots"""
      success: bool
      date: str
      available_slots: List[AvailabilitySlot] = []
      error: Optional[str] = None


  class AvailabilityRangeResponse(BaseModel):
      """Response with availability for multiple dates"""
      success: bool
      results: List[dict]  # List of date/availability info


  class CalendarStatus(BaseModel):
      """Current calendar connection status"""
      connected: bool
      calendar_id: Optional[str] = None
      email: Optional[str] = None
      connected_at: Optional[datetime] = None
      last_sync: Optional[datetime] = None


  class AppointmentCreate(BaseModel):
      """Request to create new appointment"""
      patient_id: str
      patient_name: str
      patient_phone: str
      date: str  # YYYY-MM-DD
      time: str  # HH:MM
      appointment_type: str = "General Checkup"
      notes: Optional[str] = None


  class AppointmentUpdate(BaseModel):
      """Request to update appointment"""
      date: Optional[str] = None
      time: Optional[str] = None
      appointment_type: Optional[str] = None
      notes: Optional[str] = None


  class AppointmentResponse(BaseModel):
      """Appointment information response"""
      id: str
      calendar_event_id: Optional[str] = None
      patient_id: str
      patient_name: str
      patient_phone: str
      date: str
      time: str
      duration_minutes: int
      appointment_type: str
      notes: Optional[str] = None
      status: str  # scheduled, confirmed, completed, cancelled, no_show
      reminder_sent: bool
      reminder_sent_at: Optional[datetime] = None
      created_at: datetime
      updated_at: datetime

      class Config:
          from_attributes = True


  class AppointmentCreateResponse(BaseModel):
      """Response when appointment is created"""
      success: bool
      appointment_id: str
      calendar_event_id: Optional[str] = None
      date: str
      time: str
      duration_minutes: int
      patient_name: str
      confirmation_number: str
      message: str
      sms_sent: bool


  class AppointmentCancelResponse(BaseModel):
      """Response when appointment is cancelled"""
      success: bool
      message: str
      appointment_id: str
      calendar_event_id: Optional[str] = None
      cancelled_at: datetime
      sms_sent: bool


  class CalendarEvent(BaseModel):
      """Raw Google Calendar event"""
      id: str
      summary: str
      description: Optional[str] = None
      start: str  # ISO datetime
      end: str    # ISO datetime
      location: Optional[str] = None
      hangout_link: Optional[str] = None


  class CalendarEventsResponse(BaseModel):
      """Response with raw calendar events"""
      success: bool
      events: List[CalendarEvent] = []
      error: Optional[str] = None


  class UpcomingAppointmentsResponse(BaseModel):
      """Response with list of upcoming appointments"""
      success: bool
      count: int
      appointments: List[AppointmentResponse]


  class CalendarAuthUrl(BaseModel):
      """Response containing Google Calendar auth URL"""
      auth_url: str
      state: str


  class CalendarAuthCallback(BaseModel):
      """Callback from Google OAuth"""
      code: str
      state: str


  class CalendarAuthResponse(BaseModel):
      """Response after calendar is connected"""
      success: bool
      message: str
      calendar_id: str
      email: str


  class AppointmentRemindResponse(BaseModel):
      """Response when reminder is marked as sent"""
      success: bool
      appointment_id: str
      reminder_sent: bool
      reminder_sent_at: datetime

  ---
  Summary Table

  ┌──────────────────────────────────────────────────────────────────┐
  │                    ENDPOINT SUMMARY                              │
  ├──────────────────────────────────────────────────────────────────┤
  │ GET    /api/calendar/status                 → CalendarStatus     │
  │ POST   /api/calendar/check-availability     → AvailabilityResp   │
  │ POST   /api/calendar/check-availability-    → AvailabilityRange  │
  │        range                                   Response           │
  │ POST   /api/calendar/appointments           → AppointmentCreate  │
  │                                               Response            │
  │ GET    /api/calendar/appointments           → UpcomingAppts      │
  │ GET    /api/calendar/appointments/{id}      → AppointmentResp    │
  │ PATCH  /api/calendar/appointments/{id}      → AppointmentResp    │
  │ DELETE /api/calendar/appointments/{id}      → AppointmentCancel  │
  │                                               Response            │
  │ PATCH  /api/calendar/appointments/{id}/     → AppointmentRemind  │
  │        remind                                Response            │
  │ GET    /api/calendar/events                 → CalendarEvents     │
  │                                               Response            │
  │ GET    /api/calendar/auth-url               → CalendarAuthUrl    │
  │ POST   /api/calendar/auth-callback          → CalendarAuthResp   │
  │ DELETE /api/calendar/disconnect             → Success response   │
  └──────────────────────────────────────────────────────────────────┘

  ---
  Which Endpoints Are Essential?

  For MVP, you really only need:

  1. ✅ POST /api/calendar/check-availability - Check slots
  2. ✅ POST /api/calendar/appointments - Create appointment
  3. ✅ DELETE /api/calendar/appointments/{id} - Cancel appointment
  4. ✅ GET /api/calendar/status - Check if calendar is connected
  5. ✅ GET /api/calendar/auth-url - Get OAuth URL
  6. ✅ POST /api/calendar/auth-callback - Handle OAuth callback

  The rest can be added later for the dashboard/UI.

  Want me to implement all these endpoints in src/api/main.py?