# ElevenLabs Tool Registration Guide

**Last Updated**: February 2026

## Overview

This guide explains how to register CallPilot's 5 webhook tools in ElevenLabs ConvAI agent, enabling the agent to actually call your backend endpoints instead of simulating tool executions.

## Prerequisites

1. **Backend Running**: FastAPI backend must be running on `http://localhost:8000`
2. **ngrok Tunnel**: ngrok must be exposing your backend (e.g., `https://abc-123.ngrok.io`)
3. **ElevenLabs Agent Created**: You have an active ConvAI agent in ElevenLabs

## Key Concepts

- **System Prompt Variables**: Text placeholders (e.g., `{{api_base_url}}`) - NOT actual tools
- **Webhook Tools**: Actual registered tools that agents can invoke via HTTP calls
- **Tool ID**: Internal reference used in agent configuration (if needed)
- **Parameters**: Input fields for each tool call

## Step-by-Step Registration

### 1. Navigate to Agent Tools Section

1. Log in to [ElevenLabs Console](https://console.elevenlabs.io)
2. Select your ConvAI agent
3. Click **"Tools"** in the left sidebar
4. You should see your current agent setup

### 2. Add Tool #1: check_availability

1. Click **"Add Tool"** → Select **"Webhook"**
2. Fill in the following:

**Basic Configuration:**
- **Name**: `check_availability`
- **Description**: Check available appointment times for a specific date. Use this when the patient asks about availability on a specific day.

**Webhook Configuration:**
- **URL**: `https://YOUR-NGROK-URL/api/agent/calendar/availability`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`

**Parameters:**
- **Parameter 1**:
  - Name: `date`
  - Type: `string`
  - Description: `Date to check in YYYY-MM-DD format (e.g., 2026-02-15)`
  - Required: ✓ YES

3. Click **"Save Tool"**

### 3. Add Tool #2: list_my_appointments

1. Click **"Add Tool"** → Select **"Webhook"**
2. Fill in the following:

**Basic Configuration:**
- **Name**: `list_my_appointments`
- **Description**: Retrieve all upcoming appointments for the patient. Use this when the patient asks 'what are my appointments' or 'when is my next appointment'.

**Webhook Configuration:**
- **URL**: `https://YOUR-NGROK-URL/api/agent/appointments/list`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`

**Parameters:**
- **Parameter 1**:
  - Name: `phone_number`
  - Type: `string`
  - Description: `Patient's phone number (auto-provided from incoming call)`
  - Required: ✓ YES

3. Click **"Save Tool"**

### 4. Add Tool #3: schedule_appointment

1. Click **"Add Tool"** → Select **"Webhook"**
2. Fill in the following:

**Basic Configuration:**
- **Name**: `schedule_appointment`
- **Description**: Schedule a new appointment. Use this when the patient has selected a date and time they want to book.

**Webhook Configuration:**
- **URL**: `https://YOUR-NGROK-URL/api/agent/appointments/schedule`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`

**Parameters:**
- **Parameter 1**: `phone_number` (string, required)
  - Description: `Patient's phone number`
- **Parameter 2**: `patient_name` (string, required)
  - Description: `Patient's full name`
- **Parameter 3**: `date` (string, required)
  - Description: `Appointment date in YYYY-MM-DD format`
- **Parameter 4**: `time` (string, required)
  - Description: `Appointment time in HH:MM format (e.g., 14:30)`
- **Parameter 5**: `appointment_type` (string, optional)
  - Description: `Type of appointment (e.g., General Checkup, Follow-up)`

3. Click **"Save Tool"**

### 5. Add Tool #4: reschedule_appointment

1. Click **"Add Tool"** → Select **"Webhook"**
2. Fill in the following:

**Basic Configuration:**
- **Name**: `reschedule_appointment`
- **Description**: Reschedule an existing appointment to a new date and time.

**Webhook Configuration:**
- **URL**: `https://YOUR-NGROK-URL/api/agent/appointments/reschedule`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`

**Parameters:**
- **Parameter 1**: `phone_number` (string, required)
- **Parameter 2**: `appointment_id` (string, required)
- **Parameter 3**: `new_date` (string, required)
  - Description: `New appointment date in YYYY-MM-DD format`
- **Parameter 4**: `new_time` (string, required)
  - Description: `New appointment time in HH:MM format (e.g., 14:30)`

3. Click **"Save Tool"**

### 6. Add Tool #5: cancel_appointment

1. Click **"Add Tool"** → Select **"Webhook"**
2. Fill in the following:

**Basic Configuration:**
- **Name**: `cancel_appointment`
- **Description**: Cancel an existing appointment. Use this when the patient wants to cancel an appointment.

**Webhook Configuration:**
- **URL**: `https://YOUR-NGROK-URL/api/agent/appointments/cancel`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`

**Parameters:**
- **Parameter 1**: `phone_number` (string, required)
- **Parameter 2**: `appointment_id` (string, required)

3. Click **"Save Tool"**

## Verification

After registering all 5 tools:

1. **Check Tools Section**: You should see all 5 tools listed
2. **Test a Tool**: Use ElevenLabs' tool testing feature to verify connectivity
3. **Make a Test Call**: Call your agent and ask "What appointments are available on February 17th?"
4. **Monitor Logs**: Check your backend logs (should show `[TOOL CALL]` entries if tool is being invoked)

## Debugging

### Tool Not Being Called

1. **Verify ngrok is running**: `~/.local/bin/ngrok http 8000`
2. **Check ngrok URL**: Ensure all tools use correct URL from `ngrok` output
3. **Test endpoint manually**:
   ```bash
   curl -X POST https://YOUR-NGROK-URL/api/agent/calendar/availability \
     -H "Content-Type: application/json" \
     -d '{"date":"2026-02-17"}'
   ```
4. **Check backend logs**: Should show `[TOOL CALL] check_availability called` or similar
5. **Review conversation transcript**: In ElevenLabs, check conversation history to see what agent attempted

### Tool Called But No Response

1. **Check backend endpoint logs**: Look for `[TOOL CALL]` and `[MCP PROXY]` entries
2. **Verify database connection**: Backend must have access to SQLite database
3. **Check OAuth token**: Doctor must have valid OAuth token stored
4. **Test endpoint directly**:
   ```bash
   curl -X POST https://YOUR-NGROK-URL/api/agent/appointments/list \
     -H "Content-Type: application/json" \
     -d '{"phone_number":"+1234567890"}'
   ```

### Parameter Mismatch Errors

If you see "parameter not recognized" errors:
1. Verify parameter names match exactly (case-sensitive)
2. Ensure required parameters are marked as required
3. Check parameter types (string vs integer)
4. Review tool schema in `ELEVENLABS_TOOLS_SCHEMA.json`

## System Prompt Reference

Update your agent's system prompt to reference these tools:

```
You are a helpful medical appointment scheduling assistant. You have the following tools available:

1. **check_availability** - Check what times the doctor has available on a specific date
2. **list_my_appointments** - Show the patient's upcoming scheduled appointments
3. **schedule_appointment** - Book a new appointment for the patient
4. **reschedule_appointment** - Move an appointment to a different date or time
5. **cancel_appointment** - Cancel an appointment for the patient

When a patient asks about availability, use check_availability.
When they ask about their existing appointments, use list_my_appointments.
When they want to book an appointment, first check availability, then use schedule_appointment.
When they want to reschedule, use reschedule_appointment.
When they want to cancel, use cancel_appointment.

Always be helpful and professional.
```

## Important Notes

- **NO Hardcoding**: Doctor ID is hardcoded to `"doctor_001"` in backend (single-tenant prototype)
- **Phone Numbers**: Agent automatically receives patient's phone from incoming call; you may need to manually provide it in testing
- **Confirmation Numbers**: All scheduled appointments receive a confirmation number in format `CP-YYYYMMDD-XXX`
- **Dummy Calendar**: Currently uses mock calendar (6 slots 9AM-4PM on weekdays, special rule for Monday 2/9/2026, closed weekends)
- **No Google Calendar Yet**: Google Calendar integration is marked TODO in backend

## Files Reference

- **Tool Schemas**: See `ELEVENLABS_TOOLS_SCHEMA.json` for complete JSON specifications
- **Backend Endpoints**: See `/src/api/main.py` for agent endpoint implementations
- **Service Logic**: See `/src/calendar/service.py` for business logic

## Testing Your Setup

### Test 1: Manual curl to check_availability
```bash
curl -X POST https://YOUR-NGROK-URL/api/agent/calendar/availability \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-02-17"}'
```

Expected response:
```json
{
  "success": true,
  "date": "2026-02-17",
  "available_slots": [
    {"time": "09:00", "duration_minutes": 30},
    {"time": "10:00", "duration_minutes": 30},
    ...
  ]
}
```

### Test 2: Make an inbound call
1. Call your twilio number
2. Agent should answer
3. Ask "What appointments are available on February 17th?"
4. Check backend logs for `[TOOL CALL] check_availability called`

### Test 3: Schedule an appointment via agent
1. Ask agent "I'd like to book an appointment"
2. Agent should call `check_availability` first
3. After showing options, agent should call `schedule_appointment`
4. You should receive SMS confirmation (once Twilio SMS is integrated)

## Contact & Support

For issues with:
- **Backend endpoints**: Check `/src/api/main.py`
- **Tool logic**: Check `/src/calendar/service.py`
- **Database**: Check `/src/database/models.py`
- **ElevenLabs setup**: Refer to ElevenLabs official docs at https://docs.elevenlabs.io

