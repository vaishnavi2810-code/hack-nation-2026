# CallPilot Skeleton Implementation

## Project Structure

```
hack-nation-2026/
├── main.py                          # FastAPI application with all endpoints
├── config.py                        # Configuration loader from .env
├── twilio_wrapper.py                # Twilio wrapper class for voice/SMS
├── models.py                        # Pydantic models for request/response validation
├── requirements.txt                 # Python dependencies
├── .env.example                     # Configuration template
├── .env                            # User's local config (gitignored)
├── .gitignore                      # Git ignore rules
├── README.md                       # User-facing documentation
├── CLAUDE.md                       # Claude Code guidance
├── SKELETON_STRUCTURE.md           # This file
├── google_credentials.json         # Google service account (gitignored)
├── callpilot.db                   # SQLite database (gitignored)
├── logs/                          # Application logs
│   ├── app.log
│   └── reminder.log
├── tests/                         # Unit tests (TODO)
│   ├── test_api.py
│   ├── test_calendar.py
│   └── test_twilio.py
├── migrations/                    # Database migrations (TODO)
│   └── alembic/
└── reminder_scheduler.py          # Cron job for reminders (TODO)
```

## Files Created

### 1. **config.py** - Configuration Management
- Loads all environment variables from `.env`
- Validates required variables on startup
- Provides constants for API timeouts, message templates, etc.
- **NO HARDCODED VALUES** - Everything comes from `.env` or constants
- Uses `validate_required_var()` and `get_optional_var()` helpers

### 2. **twilio_wrapper.py** - Twilio Integration
- `TwilioWrapper` class encapsulates all Twilio operations
- Methods for:
  - `handle_inbound_call()` - Route patient calls to ElevenLabs agent
  - `make_outbound_call()` - Initiate reminder/confirmation calls
  - `get_call_status()` - Check call status
  - `list_calls()` - Get recent calls
  - `send_sms()` - Send SMS confirmations
  - `hang_up_call()` - Terminate calls
  - TwiML helpers for building voice responses

### 3. **models.py** - Pydantic Models
Request/response validation for:
- Authentication (signup, login, logout)
- Doctor profile
- Calendar operations (auth, status, disconnect)
- Patients (create, read, update, delete)
- Appointments (create, update, delete, confirm)
- Calls (inbound, outbound, manual)
- Dashboard and settings
- Webhooks and callbacks

### 4. **main.py** - FastAPI Backend
Complete skeleton with all endpoints:

**Auth Endpoints** (`/api/auth`)
- `POST /signup` - Create doctor account
- `POST /login` - Authenticate and get JWT
- `POST /logout` - Logout and invalidate tokens

**Doctor Endpoints** (`/api/doctors`)
- `GET /me` - Get doctor profile

**Calendar Endpoints** (`/api/calendar`)
- `GET /auth-url` - Get Google OAuth URL
- `POST /callback` - Handle OAuth callback
- `GET /status` - Check calendar connection
- `POST /disconnect` - Disconnect calendar
- `GET /availability` - Check available slots

**Patient Endpoints** (`/api/patients`)
- `GET /` - List patients
- `POST /` - Create patient
- `GET /:id` - Get patient details
- `PUT /:id` - Update patient
- `DELETE /:id` - Delete patient

**Appointment Endpoints** (`/api/appointments`)
- `GET /` - List appointments
- `GET /upcoming` - Get upcoming appointments
- `POST /` - Create appointment
- `PUT /:id` - Update appointment
- `DELETE /:id` - Cancel appointment
- `POST /:id/confirm` - Confirm appointment

**Call Endpoints** (`/api/calls`)
- `GET /` - List calls
- `GET /scheduled` - Get scheduled calls
- `GET /:id` - Get call details
- `POST /manual` - Make manual call

**Dashboard Endpoints** (`/api/dashboard`)
- `GET /stats` - Get statistics
- `GET /activity` - Get recent activity

**Settings Endpoints** (`/api/settings`)
- `GET /` - Get settings
- `PUT /` - Update settings

**Webhook Endpoints** (`/api/webhooks`)
- `POST /elevenlabs` - ElevenLabs webhook
- `POST /twilio/voice` - Twilio voice webhook

### 5. **.env.example** - Configuration Template
Template for all required and optional configuration:
- ElevenLabs credentials
- Twilio credentials
- Google Calendar credentials
- Doctor settings
- Reminder settings
- Database URL
- Authentication secrets
- Feature flags

### 6. **requirements.txt** - Dependencies
All Python packages needed:
- FastAPI, Uvicorn (web framework)
- Twilio, ElevenLabs (integrations)
- Google Calendar API libraries
- SQLAlchemy (ORM)
- Authentication (python-jose, passlib, bcrypt)
- Utilities (python-dotenv, requests, colorama)
- Testing (pytest, pytest-asyncio)

## TODO Items

Each endpoint has TODO comments for:
1. **Authentication** - JWT token generation/validation
2. **Database** - Storing and retrieving records
3. **Google Calendar** - Creating/updating events
4. **Error Handling** - Proper validation and error responses
5. **Logging** - Comprehensive logging for debugging

## Starting the Application

```bash
# Setup
cp .env.example .env
# Edit .env with your credentials

pip install -r requirements.txt

# Run
python main.py
```

The API will be available at `http://localhost:8000`

Health check: `curl http://localhost:8000/health`

## Architecture Notes

### Three Main Components

1. **Voice Agent (ElevenLabs)**
   - Handles inbound patient calls
   - Calls backend functions for availability/booking
   - Routes via webhook to our API

2. **Backend API (FastAPI)**
   - All endpoints return placeholder responses
   - Integration points marked with TODO
   - Uses Twilio wrapper for voice/SMS
   - Ready for database integration

3. **Reminder Scheduler (TODO)**
   - Will run as separate cron job
   - Checks for upcoming appointments every 15 min
   - Triggers outbound calls 3 hours before appointment
   - Updates appointment status in Google Calendar

### Configuration Pattern

All values come from `.env` or named constants in `config.py`:

```python
# In config.py:
DOCTOR_TIMEZONE = get_optional_var("DOCTOR_TIMEZONE", "America/New_York")
REMINDER_HOURS_BEFORE = int(get_optional_var("REMINDER_HOURS_BEFORE", "3"))

# In main.py (never hardcoded):
event_duration = config.APPOINTMENT_DURATION_MINUTES
recipient_phone = patient.phone_number
```

### Error Handling

All errors return JSON responses with:
- `success: false`
- `error: string`
- `timestamp: ISO datetime`

Custom exception handlers for HTTP and general exceptions.

### Logging

Uses `colorama` for colored terminal output:
- `{Fore.GREEN}✅` - Success
- `{Fore.RED}❌` - Errors
- `{Fore.YELLOW}⚠️` - Warnings
- `{Fore.CYAN}ℹ️` - Info/Debug (if DEBUG=true)

## Next Steps

1. **Database Setup**
   - Create SQLAlchemy models for Doctor, Patient, Appointment, Call
   - Set up alembic migrations
   - Implement CRUD operations

2. **Authentication**
   - Implement JWT token generation
   - Add password hashing with bcrypt
   - Create auth middleware for protected endpoints

3. **Google Calendar Integration**
   - Implement OAuth2 flow for calendar auth
   - Create calendar event CRUD functions
   - Implement free/busy queries

4. **Reminder Scheduler**
   - Create `reminder_scheduler.py` as separate script
   - Query appointments 3 hours in advance
   - Trigger outbound calls
   - Update event status

5. **Error Handling & Validation**
   - Add request validation for all endpoints
   - Implement proper error messages
   - Add input sanitization

6. **Testing**
   - Unit tests for config, models, twilio_wrapper
   - Integration tests for API endpoints
   - Mock Twilio/ElevenLabs for testing

## Important Notes

- **NO HARDCODED VALUES** - All config from `.env` or constants
- **Placeholder Responses** - All endpoints return dummy data, ready for implementation
- **TODO Comments** - Mark exact locations where real logic needs to be added
- **Error Handling** - Basic structure in place, needs refinement
- **Security** - Passwords not implemented, JWT not validated yet
