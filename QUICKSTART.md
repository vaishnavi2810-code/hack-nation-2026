# CallPilot Quick Start

## Setup

1. **Copy environment template**
```bash
cp .env.example .env
```

2. **Edit `.env` with your credentials**
```bash
# Required (get from services):
ELEVENLABS_API_KEY=sk_your_key
ELEVENLABS_AGENT_ID=agent_your_id
TWILIO_ACCOUNT_SID=AC_your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+12125551234
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com
GOOGLE_CREDENTIALS_PATH=./google_credentials.json
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_secret
DOCTOR_EMAIL=doctor@example.com
SECRET_KEY=your_super_secret_key
```

3. **Install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run the API

```bash
python main.py
```

You should see:
```
✅ Configuration validated successfully
✅ Twilio client initialized
✅ CallPilot API initialized
✅ Starting CallPilot API...
Running on http://localhost:8000
```

## Test the API

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app": "CallPilot",
  "version": "0.1.0",
  "timestamp": "2026-02-07T12:00:00"
}
```

### Get Doctor Profile (Placeholder)
```bash
curl http://localhost:8000/api/doctors/me
```

### Create Patient (Placeholder)
```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+12025551234",
    "email": "john@example.com"
  }'
```

### Check Availability (Placeholder)
```bash
curl http://localhost:8000/api/calendar/availability \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-15"}'
```

Response:
```json
{
  "success": true,
  "date": "2026-02-15",
  "available_slots": [
    {"date": "2026-02-15", "time": "14:00", "duration_minutes": 30},
    {"date": "2026-02-15", "time": "15:00", "duration_minutes": 30},
    {"date": "2026-02-15", "time": "16:00", "duration_minutes": 30}
  ]
}
```

## API Documentation

Interactive API docs: http://localhost:8000/docs (Swagger UI)

Alternative docs: http://localhost:8000/redoc (ReDoc)

## File Overview

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app with all endpoints |
| `config.py` | Load and validate `.env` |
| `twilio_wrapper.py` | Twilio integration |
| `models.py` | Request/response schemas |
| `requirements.txt` | Python dependencies |
| `.env.example` | Configuration template |
| `.env` | Your actual config (gitignored) |

## Current Status

This is a **skeleton implementation** with:
- ✅ All endpoints defined
- ✅ Request/response schemas
- ✅ Placeholder responses
- ❌ Database not implemented
- ❌ Authentication not implemented
- ❌ Google Calendar not integrated
- ❌ Real business logic not implemented

Each endpoint has TODO comments showing what needs to be implemented.

## Next Steps

1. Set up database (SQLAlchemy models)
2. Implement authentication (JWT)
3. Implement Google Calendar integration
4. Create reminder scheduler
5. Add comprehensive error handling
6. Write tests

See `SKELETON_STRUCTURE.md` for detailed TODO items.

## Troubleshooting

### Error: "Missing required environment variables"
- Check that `.env` file exists and is in the project root
- Verify all required variables are set (no empty values)
- See `.env.example` for complete list

### Error: "Failed to initialize Twilio client"
- Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct
- Check that your Twilio account is active

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001)"
```

## Debug Mode

Enable debug logging in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

Then run:
```bash
python main.py
```

You'll see detailed [DEBUG] logs for all operations.

## Production Deployment

For production:
1. Create `.env.production` with production credentials
2. Set `DEBUG=false`
3. Use proper database (PostgreSQL recommended)
4. Use environment variables for all secrets
5. Run with ASGI server (uvicorn, gunicorn, etc.)

Example production startup:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```
