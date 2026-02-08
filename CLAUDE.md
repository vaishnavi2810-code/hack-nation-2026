# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ CRITICAL: NO HARDCODED VALUES

**EVERY value that might change must be a named variable, constant, or environment variable.**

This applies to:
- API keys, tokens, credentials (→ `.env`)
- Phone numbers, IDs, URLs (→ `.env` or config constants)
- Timezones, appointment durations, reminder times (→ `.env` or config file)
- Message text, error messages (→ constants at top of file)
- Any magic numbers (timeouts, retry counts, pagination limits) (→ named constants)

**Pattern:**
```python
# ✅ CORRECT
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "30"))
REMINDER_HOURS_BEFORE = int(os.getenv("REMINDER_HOURS_BEFORE", "3"))
DOCTOR_TIMEZONE = os.getenv("DOCTOR_TIMEZONE", "America/New_York")

# ❌ WRONG
APPOINTMENT_DURATION_MINUTES = 30
REMINDER_HOURS_BEFORE = 3
DOCTOR_TIMEZONE = "America/New_York"
```

See full details in "NO HARDCODED VALUES Rule" section below.

---

## 🔐 AUTHENTICATION: Option 2 Backend Proxy Pattern

**CallPilot implements Option 2 (Backend Proxy Pattern) for authentication.**

This means:
1. **Frontend → Backend**: User logs in with Google OAuth
2. **Backend stores OAuth token** in database (keyed by user_id)
3. **ElevenLabs agent calls backend endpoints** with JWT token in Authorization header
4. **Backend looks up user's OAuth token** from database
5. **Backend calls Calendar MCP** with that OAuth token
6. **Results returned to ElevenLabs agent**

**Why Option 2?**
- OAuth tokens stay on backend (never exposed to ElevenLabs)
- ElevenLabs doesn't need to know about authentication
- Token refresh handled transparently
- Easy to audit and monitor

**See AUTH_IMPLEMENTATION.md for detailed flow diagrams and code examples.**

---

## Project Overview

**CallPilot - AI Voice Agent for Medical Appointments**

A voice-first AI assistant powered by ElevenLabs and Twilio that handles medical appointment scheduling through natural phone conversations. Patients call to book, cancel, or reschedule appointments. All data is stored directly in Google Calendar events with SMS confirmations via Twilio.

**Key Features:**
- Inbound calls: Patients call to book/cancel/reschedule appointments
- Automated reminders: AI calls patients 3 hours before appointment
- Google Calendar integration: Doctor manages availability and views all bookings
- Natural conversation: ElevenLabs ConvAI handles all patient interactions
- SMS confirmations: Twilio sends confirmation texts after booking

---

## Architecture

### Call Flow: Patient Booking

```
Patient calls → Twilio Number → Webhook → ElevenLabs Agent
                                           ↓
                                  "How can I help?"
                                           ↓
                                  Agent checks availability
                                  (calls backend: check_availability)
                                           ↓
                                  Backend queries Google Calendar free/busy
                                           ↓
                                  Returns available slots
                                           ↓
                                  Agent offers slots to patient
                                           ↓
                                  Patient selects slot
                                           ↓
                                  Agent creates event
                                  (calls backend: book_appointment)
                                           ↓
                                  Backend creates Google Calendar event
                                  with patient details in description
                                           ↓
                                  Twilio sends SMS confirmation
                                           ↓
                                  Agent: "You're all set!"
```

### Call Flow: Automated 3-Hour Reminder

```
Cron job runs every 15 min
         ↓
Query Google Calendar for events 3h ahead
         ↓
Find appointment with phone number in metadata
         ↓
Trigger ElevenLabs outbound call via Twilio
         ↓
Patient answers
         ↓
Agent: "Hi [Name], reminder about your [Time] appointment today"
         ↓
Patient confirms or asks to reschedule
         ↓
Update event description: "Reminder Sent: true"
```

### Data Storage: Google Calendar

**Doctor's Availability:**
- Doctor creates "Available for Appointments" block in calendar
- System queries free/busy status
- Returns available time slots

**Booked Appointments:**
- Event Title: `Appointment: [Patient Name]`
- Start Time: Scheduled time
- Duration: 30 minutes (configurable)
- Description:
  ```
  Patient: John Doe
  Phone: +1234567890
  Type: Checkup
  Status: scheduled
  Reminder Sent: false
  ```

---

## Common Development Tasks

### Setup (First Time)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Running the Application

```bash
# Start the voice agent server (FastAPI/Flask)
python app.py

# In another terminal, start the reminder cron job
python reminder_scheduler.py

# Test endpoints with curl/Postman
curl -X POST http://localhost:5000/book_appointment \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+1234567890",
    "date": "2026-02-11",
    "time": "14:00"
  }'
```

### Testing the Voice Integration

```bash
# Validate setup (credentials, Google Calendar access)
python validate_setup.py

# Test inbound call (real call)
# 1. Call your Twilio number
# 2. Agent should answer
# 3. Try booking an appointment by speaking naturally

# Test outbound reminder (manual trigger)
python test_reminder.py --patient-id abc123
```

### Adding New Agent Functions

ElevenLabs agents call backend functions like `check_availability()` and `book_appointment()`. Pattern:

```python
# In your backend (app.py or similar)

@app.post("/check_availability")
def check_availability(date: str):
    """
    Called by ElevenLabs agent during conversation

    Args:
        date: User's requested date (e.g., "2026-02-11" or "next Tuesday")

    Returns:
        {
            "success": true,
            "available_slots": ["14:00", "15:00", "16:00"],
            "date": "2026-02-11"
        }
    """
    # Parse date (handle natural language like "next Tuesday")
    parsed_date = parse_date(date)

    # Query Google Calendar free/busy
    calendar_service = get_google_calendar_service()
    busy_times = calendar_service.freebusy().query(...).execute()

    # Calculate available slots (30-min blocks)
    available_slots = calculate_available_slots(parsed_date, busy_times)

    return {
        "success": True,
        "available_slots": available_slots,
        "date": parsed_date.isoformat()
    }

@app.post("/book_appointment")
def book_appointment(name: str, phone: str, date: str, time: str):
    """
    Called by ElevenLabs agent after patient confirms selection

    Args:
        name: Patient name
        phone: Patient phone number (E.164 format)
        date: Appointment date
        time: Appointment time (HH:MM)

    Returns:
        {
            "success": true,
            "event_id": "abc123xyz",
            "confirmation_number": "CP-20260211-001"
        }
    """
    # Create Google Calendar event
    event_data = {
        "summary": f"Appointment: {name}",
        "start": {"dateTime": f"{date}T{time}:00"},
        "end": {"dateTime": f"{date}T{time}:30:00"},
        "description": f"Patient: {name}\nPhone: {phone}\nType: Checkup\nStatus: scheduled\nReminder Sent: false"
    }

    calendar_service = get_google_calendar_service()
    event = calendar_service.events().insert(
        calendarId=DOCTOR_CALENDAR_ID,
        body=event_data
    ).execute()

    # Send SMS confirmation
    send_sms_confirmation(phone, name, date, time)

    # Store event_id and phone_number for reminder job
    store_appointment_metadata(event["id"], phone)

    return {
        "success": True,
        "event_id": event["id"],
        "confirmation_number": f"CP-{date.replace('-', '')}-{event['id'][:3].upper()}"
    }
```

---

## Configuration Management

### `.env` File (User's Local Config)

```bash
# ElevenLabs
ELEVENLABS_API_KEY=sk_...          # From https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_AGENT_ID=agent_...      # From ElevenLabs dashboard after creating ConvAI agent

# Twilio
TWILIO_ACCOUNT_SID=AC...           # From https://console.twilio.com/
TWILIO_AUTH_TOKEN=...              # From https://console.twilio.com/
TWILIO_PHONE_NUMBER=+1234567890    # Your Twilio phone number (E.164 format)

# Google Calendar
GOOGLE_CALENDAR_ID=...             # Doctor's calendar ID
GOOGLE_CREDENTIALS_JSON=...        # Path to Google service account JSON
                                    # OR base64-encoded JSON for production

# Application Config
DOCTOR_TIMEZONE=America/New_York    # Doctor's timezone for availability
APPOINTMENT_DURATION_MINUTES=30     # Default 30 min slots
REMINDER_HOURS_BEFORE=3             # Call patient 3 hours before

# Optional
DEBUG=false                         # Enable debug logging
```

### Loading Config in Code

**At the top of every file that uses config, do this:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Required secrets (from .env)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

# Optional config with sensible defaults
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "30"))
REMINDER_HOURS_BEFORE = int(os.getenv("REMINDER_HOURS_BEFORE", "3"))
REMINDER_CHECK_INTERVAL_SECONDS = int(os.getenv("REMINDER_CHECK_INTERVAL_SECONDS", "900"))  # 15 min
DOCTOR_TIMEZONE = os.getenv("DOCTOR_TIMEZONE", "America/New_York")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Validate all required vars
def validate_config():
    """Ensure all required environment variables are set"""
    required = [
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_AGENT_ID",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "GOOGLE_CALENDAR_ID",
        "GOOGLE_CREDENTIALS_PATH"
    ]

    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return True

# Call this on startup
validate_config()
```

Then use these constants throughout your code:
```python
# ✅ CORRECT
headers = {"xi-api-key": ELEVENLABS_API_KEY}
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
event_duration = APPOINTMENT_DURATION_MINUTES

# ❌ WRONG
headers = {"xi-api-key": os.getenv("ELEVENLABS_API_KEY")}  # Repeated env lookup
twilio_client = Client("AC123...", "token123...")  # Hardcoded
```

---

## Key Implementation Details

### Three Main Components

1. **Voice Agent (ElevenLabs)**
   - Handles inbound patient calls
   - Conversational AI for booking/canceling/rescheduling
   - Calls backend functions: `check_availability()`, `book_appointment()`, `cancel_appointment()`
   - Webhook configured in ElevenLabs Integrations → Twilio

2. **Backend API (FastAPI/Flask)**
   - Endpoints for agent to call: `/check_availability`, `/book_appointment`, `/cancel_appointment`
   - Google Calendar integration: read availability, create/update/delete events
   - SMS integration: send confirmations via Twilio
   - Runs on accessible URL (for ElevenLabs webhook)

3. **Reminder Scheduler (Cron Job)**
   - Runs every 15 minutes
   - Queries Google Calendar for events 3 hours ahead
   - Extracts phone numbers from event descriptions
   - Triggers outbound ElevenLabs calls
   - Updates event metadata after call

### Webhook Configuration (ElevenLabs)

- **URL:** Configured in ElevenLabs Integrations → Twilio
- **Receiver:** Your backend API at `/webhook` endpoint
- **Payload:** Contains call metadata (caller ID, agent ID, etc.)
- **Response:** TwiML or JSON depending on ElevenLabs SDK version

### Handling No-Shows

When doctor marks an appointment as "no-show":
1. Update event description: `Status: no_show`
2. Scheduler detects change on next run
3. Triggers outbound call to patient
4. Agent offers to reschedule
5. If patient reschedules: update event
6. If patient doesn't respond: delete event and log

### Cost Model

| Action | Cost | Notes |
|--------|------|-------|
| Inbound booking call | ~$0.54 | ElevenLabs ConvAI + Twilio (5 min avg) |
| Outbound reminder call | ~$0.54 | ElevenLabs ConvAI + Twilio (2 min avg) |
| SMS confirmation | ~$0.01 | Twilio SMS per message |
| Google Calendar | $0 | Free tier sufficient |

---

## Troubleshooting Guide

### Issue: Patient calls but hears "Configure this number"

**Cause:** Webhook not configured or not pointing to your backend

**Fix:**
1. Go to ElevenLabs → Integrations → Twilio → Connected
2. Verify webhook URL points to your backend's `/webhook` endpoint
3. Verify agent is assigned to your phone number
4. Test with: `curl -X POST https://your-backend.com/webhook -H "Content-Type: application/json" -d '{"test": true}'`

### Issue: Booking fails with "Google Calendar error"

**Cause:** Missing or invalid Google service account credentials

**Fix:**
1. Verify `GOOGLE_CREDENTIALS_JSON` in `.env` is valid JSON
2. Verify service account has access to doctor's calendar
3. Check Google Cloud Console for permission errors
4. Test with: `python -c "from google.oauth2 import service_account; service_account.Credentials.from_service_account_file('credentials.json')"`

### Issue: SMS not sending after booking

**Cause:** Twilio credentials invalid or SMS not enabled on account

**Fix:**
1. Verify `TWILIO_AUTH_TOKEN` in `.env`
2. Check https://console.twilio.com/ for account balance
3. Verify phone number format is E.164 (e.g., `+12025551234`)
4. Test with: `curl -X POST https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json`

### Issue: Reminders not being triggered

**Cause:** Scheduler not running or Google Calendar query failing

**Fix:**
1. Verify `reminder_scheduler.py` is running: `ps aux | grep reminder_scheduler`
2. Check logs for errors: `tail -f logs/reminder_scheduler.log`
3. Test manually: `python test_reminder.py --patient-id abc123`
4. Verify doctor's calendar is accessible: `python validate_setup.py`

---

## Code Patterns

### Backend Function Called by Agent

```python
@app.post("/check_availability")
def check_availability(date: str):
    """
    Called by ElevenLabs agent during booking conversation

    Returns dict that agent can parse:
    {
        "success": true/false,
        "available_slots": ["14:00", "15:00"],  # Agent reads this aloud
        "error": "Could not check calendar"     # If success=false
    }
    """
    try:
        # Do the work
        return {"success": True, "available_slots": [...]}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Google Calendar Event Creation

```python
def create_appointment_event(name, phone, date, time):
    """Create Google Calendar event with patient metadata"""

    service = build('calendar', 'v3', credentials=get_credentials())

    event = {
        'summary': f'Appointment: {name}',
        'start': {
            'dateTime': f'{date}T{time}:00',
            'timeZone': os.getenv('DOCTOR_TIMEZONE')
        },
        'end': {
            'dateTime': f'{date}T{time_add_minutes(time, 30)}:00',
            'timeZone': os.getenv('DOCTOR_TIMEZONE')
        },
        'description': f'Patient: {name}\nPhone: {phone}\nStatus: scheduled\nReminder Sent: false',
        'attendees': [
            {'email': phone}  # Store phone in attendees for easy lookup
        ]
    }

    created_event = service.events().insert(
        calendarId=os.getenv('GOOGLE_CALENDAR_ID'),
        body=event
    ).execute()

    return created_event['id']
```

### Reminder Scheduler

```python
def check_upcoming_appointments():
    """Run every 15 minutes by cron job"""

    service = build('calendar', 'v3', credentials=get_credentials())

    # Find events in next 3-4 hours
    now = datetime.datetime.utcnow()
    later = now + datetime.timedelta(hours=4)

    events = service.events().list(
        calendarId=os.getenv('GOOGLE_CALENDAR_ID'),
        timeMin=now.isoformat() + 'Z',
        timeMax=later.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    for event in events.get('items', []):
        # Check if reminder already sent
        if 'Reminder Sent: true' in event.get('description', ''):
            continue

        # Extract phone number from description
        phone = extract_phone_from_description(event['description'])

        # Trigger outbound call
        trigger_reminder_call(phone, event['summary'])

        # Update event: Reminder Sent: true
        event['description'] = event['description'].replace(
            'Reminder Sent: false',
            'Reminder Sent: true'
        )
        service.events().update(
            calendarId=os.getenv('GOOGLE_CALENDAR_ID'),
            eventId=event['id'],
            body=event
        ).execute()
```

### Colored Logging

```python
from colorama import Fore, Style, init

init(autoreset=True)

def log_success(msg):
    print(f"{Fore.GREEN}✅ {msg}")

def log_error(msg):
    print(f"{Fore.RED}❌ {msg}")

def log_warning(msg):
    print(f"{Fore.YELLOW}⚠️  {msg}")

def log_info(msg):
    print(f"{Fore.CYAN}ℹ️  {msg}")
```

---

## File Structure

```
hack-nation-2026/
├── app.py                      # Main FastAPI/Flask app with agent webhook
├── reminder_scheduler.py       # Cron job for automated reminders
├── validate_setup.py           # Verify all credentials and integrations
├── test_reminder.py            # Manual reminder testing
├── requirements.txt            # Python dependencies
├── .env.example               # Configuration template
├── .env                       # User's local config (gitignored)
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # This file
├── logs/                      # Application logs
│   ├── app.log
│   └── reminder.log
├── google_credentials.json    # Google service account (gitignored)
└── tests/                     # Unit and integration tests
    ├── test_calendar.py
    ├── test_api.py
    └── test_reminder.py
```

---

## Dependencies & Versions

```
fastapi==0.95.0              # Web framework for backend API
uvicorn==0.21.0              # ASGI server
twilio==8.10.0               # Twilio API client (calls, SMS)
elevenlabs==0.2.0            # ElevenLabs API client
google-auth-oauthlib==1.0.0  # Google Calendar auth
google-auth-httplib2==0.2.0  # Google Calendar HTTP
google-api-python-client==2.80.0  # Google Calendar API
python-dotenv==1.0.0         # Load .env files safely
requests==2.31.0             # HTTP requests
colorama==0.4.6              # Colored terminal output
APScheduler==3.10.0          # Scheduler for reminders (optional, if not using cron)
```

Update requirements.txt when adding new dependencies.

---

## NO HARDCODED VALUES Rule

**Every value that could possibly change must be a named variable, constant, or environment variable.**

### What Requires a Variable

| Value Type | Location | Example |
|------------|----------|---------|
| API keys, tokens | `.env` | `ELEVENLABS_API_KEY` |
| Phone numbers, URLs | `.env` | `TWILIO_PHONE_NUMBER`, `DOCTOR_CALENDAR_ID` |
| Timezones, durations | `.env` or config constants | `DOCTOR_TIMEZONE`, `APPOINTMENT_DURATION_MINUTES` |
| Message text | File constants | `MSG_BOOKING_CONFIRMATION`, `ERROR_CALENDAR_ACCESS` |
| Magic numbers | File constants | `REMINDER_CHECK_INTERVAL_SECONDS`, `API_TIMEOUT_SECONDS` |
| Database names, tables | `.env` | `DATABASE_NAME`, `EVENTS_TABLE` |
| Feature flags | `.env` | `ENABLE_SMS_CONFIRMATIONS`, `ENABLE_REMINDERS` |

### Why This Matters

- **Portability:** Same code works on dev, staging, production
- **Security:** Secrets never leak in git history or logs
- **Maintainability:** Change value once, everywhere updates automatically
- **Debugging:** Easy to test with different values
- **Team:** Different developers can use different configs

### Correct Pattern

```python
# At top of file
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "30"))
REMINDER_HOURS_BEFORE = int(os.getenv("REMINDER_HOURS_BEFORE", "3"))
API_TIMEOUT_SECONDS = 10  # Can add to .env later if needed
MSG_BOOKING_SUCCESS = "Your appointment has been confirmed."

# In function
event = {
    'duration': APPOINTMENT_DURATION_MINUTES,
    'reminder_time': datetime.now() - timedelta(hours=REMINDER_HOURS_BEFORE)
}

try:
    response = requests.post(url, timeout=API_TIMEOUT_SECONDS)
except:
    log_error(MSG_BOOKING_SUCCESS)
```

### Incorrect Patterns (Never Do These)

```python
# ❌ HARDCODED STRING
api_key = "sk_123abc"

# ❌ HARDCODED DEFAULT (sneaky hardcoding)
api_key = os.getenv("ELEVENLABS_API_KEY", "sk_123abc")

# ❌ MAGIC NUMBERS
time.sleep(5)  # Should be: time.sleep(SCHEDULER_CHECK_INTERVAL_SECONDS)

# ❌ MAGIC STRINGS
if event['status'] == 'scheduled':  # Should be: if event['status'] == EVENT_STATUS_SCHEDULED
    # ...

# ❌ HARDCODED PATHS
credentials = open('/home/user/google_credentials.json')  # Should be: os.getenv("GOOGLE_CREDENTIALS_PATH")

# ❌ HARDCODED URLS
requests.get('https://api.elevenlabs.io/v1/user')  # Should be: os.getenv("ELEVENLABS_API_BASE_URL")
```

---

## Testing Workflow

### Before Deployment

1. **Validate Setup:**
   ```bash
   python validate_setup.py
   ```
   - Checks `.env` completeness
   - Verifies Twilio credentials
   - Verifies ElevenLabs credentials
   - Verifies Google Calendar access
   - Verifies webhook is reachable

2. **Test Individual Endpoints:**
   ```bash
   # Start server
   python app.py

   # Test availability check
   curl -X POST http://localhost:5000/check_availability \
     -H "Content-Type: application/json" \
     -d '{"date": "2026-02-11"}'

   # Test booking
   curl -X POST http://localhost:5000/book_appointment \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "phone": "+1234567890", "date": "2026-02-11", "time": "14:00"}'
   ```

3. **Test with Real Call:**
   - Call your Twilio number
   - Try booking a test appointment
   - Verify event appears in Google Calendar
   - Verify SMS confirmation is sent

4. **Test Reminders:**
   ```bash
   python test_reminder.py --create-test-event
   python reminder_scheduler.py --run-once
   ```

---

## Common Pitfalls & Solutions

1. **Event not appearing in calendar:**
   - Verify `GOOGLE_CALENDAR_ID` is correct
   - Check service account has editor access to calendar
   - Verify event was actually created: check logs

2. **Agent says "I don't understand":**
   - Function names don't match what agent is calling
   - Function parameters don't match what agent is sending
   - Backend is returning error in response

3. **Reminders calling wrong people:**
   - Phone number extraction from event description is failing
   - Check event description format is consistent
   - Verify phone numbers are in E.164 format (+1234567890)

4. **SMS not sending:**
   - Twilio account balance too low
   - Phone number format is wrong
   - SMS service not enabled in Twilio console

---

## Future Enhancements

Possible extensions (keep in mind when designing):

1. **Multiple Doctors** - Support multiple doctors with separate calendars
2. **Cancellation/Rescheduling** - Full edit capabilities for patients
3. **Custom Availability** - Doctors set recurring availability slots
4. **No-Show Handling** - Automatic follow-up for missed appointments
5. **Call Recording** - Save call audio for quality assurance
6. **Analytics Dashboard** - View booking metrics, popular times, etc.
7. **Integration with EHR** - Connect to medical record system
8. **Payment Processing** - Charge deposits for appointments

When adding features, maintain the three-component pattern (voice, API, scheduler) and always load config from `.env`.

---

## References

- **Twilio Docs:** https://www.twilio.com/docs/voice/api
- **ElevenLabs Docs:** https://elevenlabs.io/docs
- **Google Calendar API:** https://developers.google.com/calendar/api/guides/overview
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **TwiML Reference:** https://www.twilio.com/docs/voice/twiml
- **APScheduler Docs:** https://apscheduler.readthedocs.io/ (if using for reminders)

