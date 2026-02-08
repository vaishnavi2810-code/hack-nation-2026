● Looking at the code and architecture, yes! Here are the five core modules and a comprehensive system architecture diagram:

  The Five Core Modules

  1. Core (src/core/) - Pydantic request/response validation models
  2. Database (src/database/) - SQLAlchemy ORM models and DB initialization
  3. Auth (src/auth/) - Google OAuth 2.0 flow and JWT token management
  4. Calendar (src/calendar/) - Calendar service with Backend Proxy Pattern
  5. Integrations (src/integrations/) - Twilio wrapper for voice/SMS operations

  Plus supporting modules: api/ (FastAPI routes), utils/ (helpers), and config.py (environment configuration).

  System Architecture Diagram

  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                              CALLPILOT SYSTEM ARCHITECTURE                    │
  └──────────────────────────────────────────────────────────────────────────────┘

                                      FRONTEND LAYER
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                                                                                │
  │  ┌────────────────────┐         ┌─────────────────────┐                      │
  │  │   Doctor Browser   │         │  ElevenLabs Agent   │                      │
  │  │                    │         │  (Voice AI)         │                      │
  │  │ • Google OAuth     │         │                     │                      │
  │  │ • Dashboard        │         │ • Inbound calls     │                      │
  │  │ • Patient mgmt     │         │ • Voice interaction │                      │
  │  └────────┬───────────┘         └─────────┬───────────┘                      │
  │           │                                 │                                 │
  └───────────┼─────────────────────────────────┼─────────────────────────────────┘
              │                                 │
              │ HTTP                            │ Tool Calls
              │                                 │
  ┌───────────▼──────────────────────────────────▼─────────────────────────────────┐
  │                            BACKEND LAYER (FastAPI)                             │
  │                                                                                 │
  │  ┌─────────────────────────────────────────────────────────────────────────┐  │
  │  │                          API ROUTES (src/api/)                           │  │
  │  │  • /auth/* (signup, login, logout, refresh)                             │  │
  │  │  • /calendar/* (connect, check availability, book, cancel)              │  │
  │  │  • /appointments/* (list, get, create, update, delete)                  │  │
  │  │  • /patients/* (list, get, create, update, delete)                      │  │
  │  │  • /calls/* (initiate, list, status)                                    │  │
  │  │  • /dashboard/* (stats, activity)                                       │  │
  │  └──────────────────────────────┬──────────────────────────────────────────┘  │
  │                                 │                                              │
  │        ┌────────────────────────┼────────────────────────┐                     │
  │        │                        │                        │                     │
  │  ┌─────▼──────────┐     ┌───────▼──────────┐    ┌────────▼────────┐          │
  │  │  AUTH MODULE   │     │  CALENDAR MODULE │    │ INTEGRATIONS    │          │
  │  │ (src/auth/)    │     │ (src/calendar/)  │    │ (src/integr/)   │          │
  │  │                │     │                  │    │                 │          │
  │  │ • Google OAuth │     │ BACKEND PROXY    │    │ • TwilioWrapper │          │
  │  │ • JWT tokens   │     │ PATTERN (KEY!)   │    │   - Inbound     │          │
  │  │ • Token        │     │                  │    │   - Outbound    │          │
  │  │   refresh      │     │ • Receives user  │    │   - SMS         │          │
  │  │ • User mgmt    │     │   _id from JWT   │    │                 │          │
  │  └────────────────┘     │ • Looks up OAuth │    └─────────┬────────┘          │
  │                         │   token in DB    │              │                    │
  │  ┌────────────────────┐ │ • Calls Calendar │    ┌─────────▼────────┐         │
  │  │ CORE MODULE        │ │   MCP with token │    │ REMINDER         │         │
  │  │ (src/core/)        │ │ • Returns slots  │    │ SCHEDULER        │         │
  │  │                    │ │   to agent       │    │                  │         │
  │  │ • Pydantic models  │ │                  │    │ • Periodic job   │         │
  │  │ • Request/Response │ └──────────────────┘    │ • Triggers calls │         │
  │  │ • Validation       │                         └──────────────────┘         │
  │  └────────────────────┘                                                       │
  │                                                                                 │
  │  ┌────────────────────────────────────────────────────────────────────────┐   │
  │  │                    DATABASE MODULE (src/database/)                      │   │
  │  │                                                                          │   │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │   │
  │  │  │    User      │  │   Patient    │  │ Appointment  │  │   Call    │  │   │
  │  │  │              │  │              │  │              │  │           │  │   │
  │  │  │ • id         │  │ • id         │  │ • id         │  │ • id      │  │   │
  │  │  │ • email      │  │ • doctor_id  │  │ • doctor_id  │  │ • call_sid│  │   │
  │  │  │ • name       │  │ • name       │  │ • patient_id │  │ • type    │  │   │
  │  │  │ • phone      │  │ • phone      │  │ • date       │  │ • status  │  │   │
  │  │  │ • timezone   │  │ • email      │  │ • time       │  │ • phone   │  │   │
  │  │  │ • oauth_tok  │  │ • notes      │  │ • type       │  │ • duration│  │   │
  │  │  │ • refresh_tk │  │              │  │ • status     │  │ • transcript
  │  │  │ • token_expr │  │              │  │ • reminder_  │  │           │  │   │
  │  │  │ • calendar_id│  │              │  │   sent       │  │           │  │   │
  │  │  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘  │   │
  │  │                                                                          │   │
  │  │  ┌──────────────────────────────────────────────────────────────────┐  │   │
  │  │  │              UserSession (JWT tracking)                          │  │   │
  │  │  │  • id, user_id, access_token, refresh_token, expires_at         │  │   │
  │  │  └──────────────────────────────────────────────────────────────────┘  │   │
  │  │                                                                          │   │
  │  └────────────────────────────────────────────────────────────────────────┘   │
  │                                                                                 │
  └─────────────────────────────────────────────────────────────────────────────────┘

              │                              │                           │
              │ OAuth Token                  │                           │
              │ (stored in DB,               │ Scheduled                 │
              │ NEVER in JWT)                │ Reminder Calls            │
              │                              │                           │
  ┌───────────▼──────────┐   ┌───────────────▼─────┐   ┌─────────────────▼────┐
  │   GOOGLE OAUTH       │   │  GOOGLE CALENDAR    │   │   TWILIO             │
  │   PROVIDER           │   │  MCP SERVER         │   │                      │
  │                      │   │                     │   │ • Outbound calls     │
  │ • Authorization      │   │ • get_available_    │   │ • Inbound handling   │
  │ • Access tokens      │   │   slots             │   │ • SMS confirmations  │
  │ • Refresh tokens     │   │ • create_event      │   │ • Call recordings    │
  │                      │   │ • delete_event      │   │                      │
  └──────────────────────┘   └─────────────────────┘   └──────────────────────┘


  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                          BACKEND PROXY PATTERN (KEY)                          │
  │                                                                                │
  │  ElevenLabs Agent calls:        Backend (with OAuth Token):                   │
  │  POST /api/calendar/check-availability                                        │
  │  {                              1. Receives JWT (user_id only)                │
  │    "user_id": "user_abc123"     2. Looks up user_id in database              │
  │  }                              3. Retrieves google_oauth_token from User     │
  │                                 4. Calls Calendar MCP with OAuth token        │
  │  ◄────────────────────────────  5. Returns available slots to agent          │
  │  {                                                                             │
  │    "available_slots": [...]     Benefits:                                    │
  │  }                              • OAuth tokens never exposed to ElevenLabs    │
  │                                 • Centralized token management               │
  │                                 • Token refresh happens in backend            │
  │                                 • Audit trail in database                     │
  │                                                                                │
  └──────────────────────────────────────────────────────────────────────────────┘


                             DATA FLOW: Doctor Login
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                                                                                │
  │ 1. Doctor clicks "Login with Google" → GET /auth/google/authorize             │
  │    └─ Returns Google OAuth URL + state token                                 │
  │                                                                                │
  │ 2. Doctor redirected to Google → Authorizes → Returns code                   │
  │                                                                                │
  │ 3. GET /auth/google/callback?code=...&state=...                              │
  │    └─ Auth service exchanges code for OAuth token                            │
  │    └─ Calls Google to get user info (email, name)                            │
  │    └─ Creates or updates User in DB with oauth_token, refresh_token          │
  │    └─ Creates JWT session                                                    │
  │    └─ Returns JWT to doctor                                                  │
  │                                                                                │
  │ 4. Doctor authenticated! Can now call API with JWT                           │
  │    Authorization: Bearer eyJhbGci...                                          │
  │                                                                                │
  └──────────────────────────────────────────────────────────────────────────────┘


                      DATA FLOW: ElevenLabs Books an Appointment
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                                                                                │
  │ 1. Patient calls doctor's phone number → Twilio → ElevenLabs agent           │
  │                                                                                │
  │ 2. Agent: "What date would you like?" → Patient: "Next Tuesday"              │
  │    Agent calls: POST /api/calendar/check-availability                        │
  │    {                                                                           │
  │      "user_id": "user_abc123",      ◄─ From JWT                              │
  │      "date": "2026-02-18"                                                     │
  │    }                                                                           │
  │                                                                                │
  │ 3. Calendar service receives request:                                         │
  │    ├─ Gets JWT, extracts user_id                                             │
  │    ├─ Queries User from DB, retrieves google_oauth_token                     │
  │    ├─ Calls Calendar MCP with OAuth token                                    │
  │    └─ Returns available slots to agent                                       │
  │                                                                                │
  │ 4. Agent presents slots to patient, patient confirms:                        │
  │    Agent calls: POST /api/appointments                                       │
  │    {                                                                           │
  │      "user_id": "user_abc123",      ◄─ From JWT                              │
  │      "patient_name": "John Doe",                                             │
  │      "patient_phone": "+1234567890",                                         │
  │      "date": "2026-02-18",                                                    │
  │      "time": "14:00"                                                          │
  │    }                                                                           │
  │                                                                                │
  │ 5. Calendar service:                                                         │
  │    ├─ Creates event in Google Calendar via MCP (with OAuth token)            │
  │    ├─ Creates Appointment record in database                                 │
  │    ├─ Sends SMS via Twilio confirming appointment                            │
  │    └─ Returns confirmation to agent                                          │
  │                                                                                │
  │ 6. Agent confirms to patient, call ends                                      │
  │                                                                                │
  └──────────────────────────────────────────────────────────────────────────────┘


                      TECHNOLOGY STACK
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ Backend:         FastAPI (Python web framework)                               │
  │ ORM:             SQLAlchemy (database abstraction)                            │
  │ Validation:      Pydantic (request/response schemas)                          │
  │ Authentication:  Google OAuth 2.0 + JWT                                       │
  │ Database:        SQLite (dev) / PostgreSQL (prod)                             │
  │ Voice Agent:     ElevenLabs ConvAI                                            │
  │ SMS/Voice:       Twilio                                                        │
  │ Calendar:        Google Calendar MCP Server                                   │
  │ Deployment:      Docker (planned)                                             │
  └──────────────────────────────────────────────────────────────────────────────┘

  Module Relationships

  ┌─────────────────────────────────────────────────────────────────┐
  │                    Import Dependencies                           │
  │                                                                   │
  │  config.py (shared by all)                                      │
  │      ▲                                                            │
  │      │                                                            │
  │  ┌───┴──────┬───────────┬───────────┬──────────────┐            │
  │  │           │           │           │              │            │
  │  v           v           v           v              v            │
  │ Core      Auth      Calendar   Integrations    Database          │
  │Module    Module     Module      (Twilio)       Module            │
  │  │         │          │            │             │              │
  │  └─────────┴──────────┴────────────┴─────────────┘              │
  │           │                                                       │
  │           v                                                       │
  │     API Routes                                                    │
  │    (depend on all)                                               │
  │                                                                   │
  └─────────────────────────────────────────────────────────────────┘

  Key Design Principle: Backend Proxy Pattern

  The Backend Proxy Pattern (Option 2) is the critical security architecture:

  ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
  │ ElevenLabs   │              │  CallPilot   │              │   Google     │
  │   Agent      │              │   Backend    │              │   Calendar   │
  │              │              │              │              │    MCP       │
  │ • Has JWT    │              │ • Has OAuth  │              │ • Validates  │
  │   (no token) │◄─Tool Call──►│   Token      │◄─API Call──►│   OAuth      │
  │ • Calls      │   {user_id}  │ • Looks up   │   {token}   │ • Returns    │
  │   /api/*     │              │   token      │              │   data       │
  │ • Never sees │              │ • Makes MCP  │              │              │
  │   OAuth      │              │   call       │              │              │
  │   token      │              │ • Returns    │              │              │
  │              │              │   data       │              │              │
  └──────────────┘              └──────────────┘              └──────────────┘

  Advantage: OAuth tokens NEVER exposed to untrusted agents.
            All token management centralized in backend.
            Token refresh happens automatically.