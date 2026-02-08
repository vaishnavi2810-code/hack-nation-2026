# Option 2: Backend Proxy Pattern - Authentication Implementation

## Overview

This document describes the implemented authentication flow for CallPilot using **Option 2: Backend Proxy Pattern**.

The key insight of Option 2 is that the **backend acts as a proxy** between ElevenLabs and the Google Calendar MCP Server. This centralizes authentication and keeps sensitive OAuth tokens secure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Browser)                             │
│  • User clicks "Login with Google"                                       │
│  • Redirects to Google OAuth                                             │
│  • User authenticates                                                    │
│  • Google redirects back with authorization code                         │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ [Authorization Code]
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Backend (Your Server) - PROXY LAYER                    │
│                                                                          │
│  Step 1: Exchange Code for OAuth Token                                  │
│  • Receive auth code from Google                                        │
│  • Exchange code for access_token + refresh_token                       │
│  • Store encrypted tokens in database                                   │
│                                                                          │
│  Step 2: Create JWT Session                                             │
│  • Generate JWT token (for API access)                                  │
│  • Generate refresh token (for token renewal)                           │
│  • Return to frontend                                                   │
│                                                                          │
│  Step 3: Proxy Tool Calls                                               │
│  • ElevenLabs agent calls tool (e.g., check_availability)              │
│  • Backend looks up user_id from JWT                                    │
│  • Retrieve user's OAuth token from database                            │
│  • Call Calendar MCP with OAuth token                                   │
│  • Return results to agent                                              │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ [API Calls with JWT]
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   ElevenLabs Agent (Remote AI)                          │
│  • Listens to patient calls                                             │
│  • Calls backend tools (not Calendar MCP directly)                      │
│  • Sends JWT token in Authorization header                              │
│  • Receives data back from backend                                      │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ [Tool Calls with OAuth Token]
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Google Calendar MCP Server (@cocal/google-calendar-mcp)     │
│  • Called only by backend (never by ElevenLabs directly)                │
│  • Receives user's OAuth token from backend                             │
│  • Queries/modifies calendar                                            │
│  • Returns results to backend                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Models

### User Model (Doctor)

```python
class User(Base):
    id: str                          # user_123
    email: str                       # doctor@example.com
    name: str                        # Dr. John Smith
    phone: str                       # +1234567890
    timezone: str                    # America/New_York

    # OAuth Token Storage (ENCRYPTED)
    google_oauth_token: str          # JSON: {access_token, refresh_token, ...}
    google_refresh_token: str        # For renewing expired tokens
    google_token_expiry: datetime    # When access_token expires
    google_calendar_id: str          # User's calendar ID

    # Status
    is_active: bool
    created_at: datetime
```

**Key Point:** OAuth tokens are stored in the database **keyed by user_id**. When ElevenLabs makes a tool call with user_id in the JWT, we can look up the OAuth token.

### UserSession Model

```python
class UserSession(Base):
    id: str                  # sess_abc123
    user_id: str             # Reference to User
    access_token: str        # JWT token
    refresh_token: str       # JWT refresh token
    is_active: bool
    expires_at: datetime
```

**Key Point:** Sessions track active JWT tokens, separate from OAuth tokens.

### Patient Model

```python
class Patient(Base):
    id: str
    doctor_id: str           # Reference to User (doctor)
    name: str
    phone: str
    email: str
    notes: str
```

### Appointment Model

```python
class Appointment(Base):
    id: str
    doctor_id: str           # Which doctor's calendar
    patient_id: str          # Which patient
    calendar_event_id: str   # Google Calendar event ID
    date: str                # YYYY-MM-DD
    time: str                # HH:MM
    duration_minutes: int
    status: str              # scheduled, completed, cancelled, etc.
    reminder_sent: bool
    created_at: datetime
```

## Authentication Flow

### 1. Frontend: Doctor Login with Google

```
Frontend                          Backend
  │                                │
  ├─ GET /api/auth/google/url ────>│
  │  (Request OAuth URL)            │
  │                                │
  │<─ {auth_url, state} ────────────┤
  │                                │
  ├─ Redirect to Google OAuth      │
  │  (User authenticates)           │
  │                                │
  └─ Google redirects to callback ─>│ /api/auth/google/callback
       with code                    │
                                   │
                              Exchange code for token
                              Store token in database
                              Create JWT session
                                   │
                                   ├─> Google: get user info
                                   │
                                   ├─> Database: save User + OAuth token
                                   │
                                   ├─> Database: create UserSession
                                   │
  ┌──────────────────────────────────┤
  │                                  │
  │<─ {access_token, refresh_token}──┤
  │   (JWT tokens for API access)     │
  │                                  │
  ├─ Store in localStorage           │
  │ (or secure cookie)               │
  │                                  │
  ✅ Doctor is logged in!
```

### 2. Backend: Store OAuth Token

When the doctor authenticates with Google, we:

1. Exchange authorization code for Google OAuth token
2. Create User record (or update if exists)
3. **Encrypt and store OAuth token in database**
4. Create JWT session tokens for API access

```python
# In auth_service.py
def create_or_update_user(db, email, name, oauth_token_data):
    user = User(
        id="user_xxx",
        email=email,
        name=name,
        google_oauth_token=json.dumps(oauth_token_data),  # ← STORED HERE
        google_refresh_token=oauth_token_data["refresh_token"],
        google_token_expiry=datetime.fromisoformat(oauth_token_data["expiry"])
    )
    db.add(user)
    db.commit()
    return user
```

### 3. ElevenLabs Agent: Call Tool Endpoint

When ElevenLabs agent needs to check availability:

```
Patient asks: "Am I free tomorrow at 2pm?"
                           │
                           ▼
         ElevenLabs Agent (understands question)
                           │
                           ├─ Decides to call: check_availability
                           │
                           ▼
         POST /api/calendar/check-availability
         Headers: Authorization: Bearer {JWT_TOKEN}
         Body: {"date": "2026-02-15"}
                           │
                           ▼
                      Backend receives call
```

### 4. Backend Proxy: Lookup Token & Call Calendar MCP

```python
@app.post("/api/calendar/check-availability")
async def check_availability_endpoint(
    request: AvailabilityRequest,
    current_user: str = Depends(get_current_user),  # ← Extract user_id from JWT
    db: Session = Depends(get_db)
):
    # Step 1: Look up user
    user = get_user_by_id(db, current_user)

    # Step 2: Get OAuth token from database
    oauth_token = get_user_oauth_token(db, current_user)
    # oauth_token = {"access_token": "ya29.xxx...", "refresh_token": "...", ...}

    # Step 3: Call Calendar MCP with OAuth token
    result = calendar_service.check_availability(
        user_id=current_user,
        db=db,
        date=request.date
    )

    # Inside calendar_service.check_availability:
    # - Gets oauth_token from database
    # - Creates headers: Authorization: Bearer {access_token}
    # - Calls Calendar MCP
    # - Returns results

    # Step 4: Return to agent
    return {
        "success": True,
        "date": "2026-02-15",
        "available_slots": [...]
    }
```

## Key Files

### database.py

Defines all SQLAlchemy models:
- `User` - Doctor with OAuth tokens
- `Patient` - Patient records
- `Appointment` - Appointments
- `Call` - Call records
- `UserSession` - Active sessions

### auth_service.py

Handles authentication:

**Google OAuth:**
- `get_google_oauth_url()` - Generate OAuth URL
- `exchange_oauth_code_for_token()` - Exchange code for token
- `get_user_info_from_google()` - Get user info from Google

**User Management:**
- `create_or_update_user()` - Create user with OAuth token
- `get_user_by_id()`, `get_user_by_email()` - Query users

**Token Management:**
- `get_user_oauth_token()` - Get and refresh OAuth token if needed
- `refresh_user_oauth_token()` - Refresh expired OAuth token

**JWT Management:**
- `create_access_token()` - Create JWT
- `create_refresh_token()` - Create refresh JWT
- `verify_token()` - Validate JWT

**Session Management:**
- `create_session()` - Create UserSession with tokens
- `get_session()` - Get active session
- `invalidate_session()` - Logout

### calendar_service.py

Implements backend proxy pattern:

```python
def check_availability(user_id, db, date):
    """
    Backend receives call from ElevenLabs with user_id in JWT.
    Looks up OAuth token from database.
    Calls Calendar MCP with that token.
    Returns results to agent.
    """
    oauth_token = auth_service.get_user_oauth_token(db, user_id)
    # ← OAuth token from database

    headers = {
        "Authorization": f"Bearer {oauth_token['access_token']}",
        "Content-Type": "application/json"
    }

    # Call Calendar MCP with headers
    # result = requests.post(..., headers=headers)

    return result
```

### main.py

API endpoints:

**Authentication:**
- `GET /api/auth/google/url` - Get OAuth URL
- `POST /api/auth/google/callback` - Handle OAuth callback
- `POST /api/auth/logout` - Logout

**Calendar (Backend Proxy):**
- `GET /api/calendar/status` - Check if calendar connected
- `POST /api/calendar/check-availability` - Check available slots
- `POST /api/calendar/disconnect` - Disconnect calendar

**Appointments:**
- `POST /api/appointments` - Create appointment (calls Calendar MCP)
- `GET /api/appointments/upcoming` - Get upcoming appointments

## Security Considerations

### 1. OAuth Token Storage

**Stored in database, keyed by user_id:**
- ✅ Only backend can access (not ElevenLabs or frontend)
- ✅ Can be encrypted at rest
- ✅ Can be refreshed transparently
- ❌ Database must be secured

### 2. JWT Tokens

**Sent to ElevenLabs agent:**
- ✅ Lightweight, stateless
- ✅ Can be revoked by invalidating session
- ✅ Short expiry time (30 min by default)
- ❌ Must be sent in Authorization header, not in URL

### 3. Token Refresh

**Automatic OAuth token refresh:**
- OAuth tokens expire after ~1 hour
- Our backend detects expiry and refreshes automatically
- Refresh token stored separately in database

```python
def get_user_oauth_token(db, user_id):
    user = get_user_by_id(db, user_id)
    token_data = json.loads(user.google_oauth_token)

    # Check if expired
    if user.google_token_expiry < datetime.utcnow():
        # Refresh automatically
        refresh_user_oauth_token(db, user_id)
        # Reload token
        token_data = json.loads(user.google_oauth_token)

    return token_data
```

### 4. ElevenLabs Configuration

ElevenLabs agent tools should be configured to call **your backend**, not Calendar MCP directly:

```json
{
  "tool": {
    "name": "check_calendar_availability",
    "description": "Check available appointment slots",
    "endpoint": "https://your-backend.com/api/calendar/check-availability",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer {agent_context_token}"
    }
  }
}
```

## Data Flow: Patient Books Appointment

```
Patient: "Can I book an appointment tomorrow at 2pm?"
                         │
                         ▼
         ElevenLabs Agent (hears request)
                         │
                         ├─ Calls: check_availability
                         │  Tool Call → POST /api/calendar/check-availability
                         │  JWT: {user_id: "user_123"}
                         │
                         ▼
                    Backend receives:
                    • user_id from JWT
                    • date: "tomorrow" (agent parses to 2026-02-15)
                         │
                         ├─ Look up user_id in database
                         ├─ Get OAuth token: {access_token: "ya29.xxx", ...}
                         ├─ Call Calendar MCP with token
                         ├─ Get available slots: [14:00, 15:00, 16:00]
                         │
                         ▼
         Agent: "I have 2pm, 3pm, or 4pm available"
                         │
         Patient: "2pm works for me"
                         │
                         ▼
         Agent calls: book_appointment
         Tool Call → POST /api/appointments
         JWT: {user_id: "user_123"}
         Body: {patient_name: "John", patient_phone: "+1234567890",
                date: "2026-02-15", time: "14:00"}
                         │
                         ▼
                    Backend receives:
                    • user_id from JWT
                    • patient details from body
                         │
                         ├─ Create Patient record if needed
                         ├─ Get OAuth token from database
                         ├─ Call Calendar MCP: create_event
                         ├─ Save Appointment to database
                         ├─ Send SMS confirmation
                         │
                         ▼
         Agent: "You're all set! Check your text for confirmation"
         Patient receives SMS: "Hi John, your appointment is confirmed
         for 2026-02-15 at 14:00"
```

## Configuration

### .env Variables

```bash
# Google OAuth (user authenticates with Google)
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx

# API Configuration
API_BASE_URL=http://localhost:8000
WEBHOOK_URL=http://localhost:8000/api/webhooks/elevenlabs

# JWT Tokens
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Doctor Settings
DOCTOR_TIMEZONE=America/New_York
DOCTOR_EMAIL=doctor@example.com
```

## Testing the Flow

### 1. Get OAuth URL

```bash
curl http://localhost:8000/api/auth/google/url
```

Response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random_state_token"
}
```

### 2. User Authenticates (Manual Step)

1. Open the auth_url in browser
2. Login with Google account
3. Grant calendar permissions
4. Google redirects to: `http://localhost:8000/api/auth/google/callback?code=xxx&state=xxx`

### 3. Backend Receives Callback

Backend automatically:
- Exchanges code for OAuth token
- Stores in database
- Creates JWT session
- Redirects to frontend (or returns tokens)

### 4. Use JWT to Call Endpoints

```bash
curl -X POST http://localhost:8000/api/calendar/check-availability \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-15"}'
```

Backend:
1. Validates JWT → extracts user_id
2. Looks up user's OAuth token from database
3. Calls Calendar MCP with OAuth token
4. Returns results

## Summary

**Option 2: Backend Proxy Pattern**

✅ **Benefits:**
- OAuth tokens never leave backend (secure)
- ElevenLabs doesn't handle sensitive credentials
- Token refresh handled transparently
- Centralized authentication logic
- Easy to audit and monitor

❌ **Trade-offs:**
- Slightly more latency (extra hop)
- More database queries
- Backend must be highly available

This is the **recommended approach** for multi-tier architectures where different services need to share authentication context.
