# API Development Rules - AIDN

**Purpose:** Task-specific rules for working on AIDN FastAPI backend. Load this when creating endpoints, modifying API logic, or integrating with dashboard.

---

## 🏗️ Architecture Overview

AIDN API is a **minimal FastAPI backend** that serves the Next.js dashboard and orchestrates voice agent calls.

```
Dashboard (Next.js)
        ↓ HTTP/REST
    FastAPI API (Port 8000)
        ↓
    ├── PostgreSQL (via Repository pattern)
    └── LiveKit API (agent dispatch)
```

**Key Principle:** API is a thin orchestration layer. Business logic lives in repositories and agents.

---

## 📦 Project Structure

```
src/api/
└── server.py         # FastAPI app, endpoints

src/shared/
├── database/         # Database connection & repositories
│   ├── connection.py
│   ├── repository.py
│   └── schema.sql
└── models/           # Pydantic models (Lead, Agent, etc.)
    ├── lead.py
    ├── agent.py
    └── appointment.py
```

---

## 🔧 FastAPI Conventions

### 1. Always Use Async/Await

**✅ Correct:**
```python
@app.get("/leads")
async def get_leads(limit: int = 100):
    rows = await db_manager.fetch(query, limit)
    return [dict(row) for row in rows]
```

**❌ Wrong:**
```python
@app.get("/leads")
def get_leads(limit: int = 100):  # Missing async
    rows = db_manager.fetch(query, limit)  # Missing await
    return [dict(row) for row in rows]
```

**Why:** All I/O operations (database, API calls) must be async for performance.

---

### 2. Startup Events for Database Connection

**Pattern:**
```python
db_manager: DatabaseManager = None

@app.on_event("startup")
async def startup():
    global db_manager
    db_manager = DatabaseManager()
    await db_manager.connect()
```

**Why:** 
- Initialize database connection pool once at startup
- Reuse connection across all requests
- Graceful shutdown handling

---

### 3. CORS Configuration

**Always configure CORS for local development:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dashboard
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

**Production:** Replace with actual domain or use environment variable.

---

## 📝 Pydantic Models for Validation

### Request Models

**Always validate incoming data with Pydantic:**
```python
from pydantic import BaseModel
from typing import Optional

class CallRequest(BaseModel):
    lead_id: str
    agent_id: Optional[str] = None
```

**Why:**
- Automatic validation
- Type safety
- Auto-generated API docs
- Clear contract for frontend

### Response Models

**Use response_model for consistent outputs:**
```python
class CallResponse(BaseModel):
    status: str
    call_id: str
    lead_id: str

@app.post("/calls/initiate", response_model=CallResponse)
async def initiate_call(request: CallRequest):
    # ...
    return CallResponse(
        status="dispatched",
        call_id=room_name,
        lead_id=request.lead_id,
    )
```

**Benefits:**
- Type-checked responses
- Auto-generates OpenAPI schema
- Frontend knows exactly what to expect

---

## 🗄️ Database Access: Repository Pattern Only

### ✅ Correct: Use Repository

```python
from ..shared.database import LeadRepository

lead_repo = LeadRepository(db_manager)
lead = await lead_repo.get_lead_by_id(lead_id)
```

### ❌ Wrong: Raw SQL in Endpoint

```python
# Don't do this:
rows = await db_manager.fetch("SELECT * FROM leads WHERE id = $1", lead_id)
```

**Why:**
- Repositories encapsulate database logic
- Easier to test
- Consistent error handling
- Can swap database implementations

**Exception:** Simple `GET /leads` endpoint uses raw query (acceptable for MVP, refactor later).

---

## 🚨 Error Handling

### Use HTTPException for All Errors

**Pattern:**
```python
from fastapi import HTTPException

# 400 Bad Request - Client error
if not valid_format:
    raise HTTPException(status_code=400, detail="Invalid lead_id format")

# 404 Not Found - Resource doesn't exist
if not lead:
    raise HTTPException(status_code=404, detail="Lead not found")

# 500 Internal Server Error - Server error
try:
    result = await dangerous_operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")
```

### Error Response Format

**FastAPI automatically returns:**
```json
{
  "detail": "Lead not found"
}
```

**For multiple errors:**
```python
raise HTTPException(
    status_code=400,
    detail={
        "errors": [
            {"field": "lead_id", "message": "Invalid UUID format"},
            {"field": "agent_id", "message": "Agent not found"}
        ]
    }
)
```

### Never Expose Internal Errors

**❌ Bad:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Exposes stack trace
```

**✅ Good:**
```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.error(f"Database error: {e}", exc_info=True)  # Log full error
    raise HTTPException(status_code=500, detail="Database operation failed")  # Generic message to client
```

---

## 📡 Endpoint Structure

### Naming Conventions

**RESTful patterns:**
```python
GET    /leads              # List resources
GET    /leads/{lead_id}    # Get single resource
POST   /leads              # Create resource
PUT    /leads/{lead_id}    # Update resource (full)
PATCH  /leads/{lead_id}    # Update resource (partial)
DELETE /leads/{lead_id}    # Delete resource

# Actions (non-CRUD)
POST   /calls/initiate     # Initiate a call (action)
POST   /leads/upload       # Upload leads (action)
```

### Query Parameters vs Path Parameters

**Path Parameters:** Resource identifiers
```python
@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    pass
```

**Query Parameters:** Filters, pagination, options
```python
@app.get("/leads")
async def get_leads(
    agent_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    county: Optional[str] = None
):
    pass
```

---

## 🔄 Current Endpoints

### GET /leads

**Purpose:** Fetch active leads for dashboard

**Query Parameters:**
- `agent_id` (optional): Filter by agent
- `limit` (optional): Max results (default: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "first_name": "John",
    "last_name": "Smith",
    "phone": "+15551234567",
    "address": "123 Oak St",
    "city": "Chicago",
    "county": "Cook",
    "state": "IL",
    "zip_code": "60601",
    "lead_type": "final_expense",
    "call_outcome": "fresh",
    "is_active": true,
    "created_at": "2026-01-27T10:00:00Z"
  }
]
```

**Implementation Notes:**
- Returns only `is_active = true` leads
- Ordered by `created_at DESC` (newest first)
- Currently uses raw SQL (acceptable for MVP)
- TODO: Refactor to use LeadRepository

---

### POST /calls/initiate

**Purpose:** Trigger outbound call to a lead

**Request:**
```json
{
  "lead_id": "uuid",
  "agent_id": "uuid"  // optional
}
```

**Response:**
```json
{
  "status": "dispatched",
  "call_id": "call-79199dd6-20260127153045",
  "lead_id": "79199dd6-2e54-41fb-ab47-44a8809031c6"
}
```

**Flow:**
1. Validate `lead_id` format (must be UUID)
2. Fetch lead from database via `LeadRepository`
3. Return 404 if lead not found
4. Create LiveKit room
5. Dispatch `aidn-outbound` agent with metadata
6. Return call details

**Error Cases:**
- 400: Invalid lead_id format
- 404: Lead not found
- 500: LiveKit API failure

---

### GET /agent/settings (TODO - High Priority)

**Purpose:** Fetch agent configuration (schedule, appointments, territory)

**Query Parameters:**
- `agent_id` (optional): Specific agent ID (defaults to authenticated agent)

**Response:**
```json
{
  "agent_id": "uuid",
  "schedule": {
    "monday": {
      "enabled": true,
      "time_slots": [
        { "start_time": "09:00", "end_time": "12:00" },
        { "start_time": "14:00", "end_time": "17:00" }
      ]
    },
    "tuesday": { "enabled": true, "time_slots": [...] },
    // ... other days
  },
  "appointments": {
    "max_appointments_per_day": {
      "monday": 4,
      "tuesday": 5,
      // ... other days
    },
    "earliest_appointment_time": "09:00",
    "latest_appointment_time": "18:00",
    "gap_between_appointments_hours": 2.0
  },
  "territory": {
    "counties": ["Cook", "Lake"],
    "lead_types": ["final_expense", "mortgage_protection"]
  }
}
```

**Implementation Notes:**
- Queries `agent_availability` table for schedule
- Queries `agent_profiles` for appointment settings
- Queries `agent_territories` for territory preferences
- Use `AgentRepository` to fetch data

---

### PUT /agent/settings (TODO - High Priority)

**Purpose:** Update agent configuration

**Request:**
```json
{
  "schedule": {
    "monday": {
      "enabled": true,
      "time_slots": [{ "start_time": "09:00", "end_time": "12:00" }]
    },
    // ... other days
  },
  "appointments": {
    "max_appointments_per_day": { "monday": 4, "tuesday": 5 },
    "earliest_appointment_time": "09:00",
    "latest_appointment_time": "18:00",
    "gap_between_appointments_hours": 2.0
  },
  "territory": {
    "counties": ["Cook", "Lake"],
    "lead_types": ["final_expense", "mortgage_protection"]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Settings updated successfully",
  "settings": { /* full settings object */ }
}
```

**Validation:**
- At least one day enabled
- Time slots don't overlap within day
- Max appointments per day >= 0
- At least one county selected
- At least one lead type selected
- earliest_appointment_time < latest_appointment_time
- gap_between_appointments_hours between 0.5 and 4.0

**Implementation Flow:**
1. Validate incoming settings
2. Use database transaction to update:
   - `agent_availability` (schedule)
   - `agent_profiles` (appointment settings)
   - `agent_territories` (territory preferences)
3. Return updated settings
4. Trigger slot regeneration (call `generate_appointment_slots()` stored procedure)

**Error Cases:**
- 400: Validation error (invalid time slots, overlapping times, etc.)
- 404: Agent not found
- 500: Database update failed

---

### GET /agent/available-counties (TODO)

**Purpose:** Get list of unique counties from leads table (for dropdown population)

**Response:**
```json
{
  "counties": [
    { "name": "Cook", "lead_count": 150 },
    { "name": "Lake", "lead_count": 75 },
    { "name": "DuPage", "lead_count": 120 }
  ]
}
```

**Implementation:**
```python
query = """
SELECT county, COUNT(*) as lead_count
FROM leads
WHERE is_active = true
GROUP BY county
ORDER BY lead_count DESC
"""
```

---

## 🧪 Testing Strategy

### 3 Levels of Testing

1. **Manual Testing** - curl/Postman (fast iteration)
2. **Unit Tests** - pytest (automated, CI/CD)
3. **Integration Tests** - Full request → database → response

### Manual Testing (Development)

**Test Before Dashboard Integration**

**Example: Test GET /leads**
```bash
# Basic request
curl http://localhost:8000/leads?limit=5

# With agent filter
curl http://localhost:8000/leads?agent_id=79199dd6-2e54-41fb-ab47-44a8809031c6

# Pretty print JSON
curl http://localhost:8000/leads | jq
```

**Example: Test POST /calls/initiate**
```bash
curl -X POST http://localhost:8000/calls/initiate \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "79199dd6-2e54-41fb-ab47-44a8809031c6"}' | jq
```

**Check:**
- ✅ Returns correct status code (200, 400, 404, 500)
- ✅ Response format matches schema
- ✅ Database updated correctly
- ✅ Logs show expected behavior

### Unit Tests (pytest)

**Location:** `tests/test_api.py`

**Test GET /leads endpoint:**
```python
import pytest
from httpx import AsyncClient
from src.api.server import app

@pytest.mark.asyncio
async def test_get_leads_success():
    """Test successful leads retrieval"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/leads?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    
    # Verify lead structure
    if len(data) > 0:
        lead = data[0]
        assert "id" in lead
        assert "first_name" in lead
        assert "phone" in lead
        assert "is_active" in lead

@pytest.mark.asyncio
async def test_get_leads_with_agent_filter():
    """Test filtering by agent_id"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/leads?agent_id=test-uuid")
    
    assert response.status_code == 200
    # All leads should have same agent_id (if implementation filters correctly)
```

**Test POST /calls/initiate endpoint:**
```python
@pytest.mark.asyncio
async def test_initiate_call_success(test_lead_id):
    """Test successful call initiation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/calls/initiate",
            json={"lead_id": test_lead_id}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "call_id" in data
    assert "status" in data
    assert data["status"] == "dispatched"

@pytest.mark.asyncio
async def test_initiate_call_invalid_lead_id():
    """Test error handling for invalid lead_id"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/calls/initiate",
            json={"lead_id": "not-a-uuid"}
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "invalid" in data["detail"].lower()

@pytest.mark.asyncio
async def test_initiate_call_lead_not_found():
    """Test 404 when lead doesn't exist"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/calls/initiate",
            json={"lead_id": fake_uuid}
        )
    
    assert response.status_code == 404
```

**Test error handling:**
```python
@pytest.mark.asyncio
async def test_database_error_handling(monkeypatch):
    """Test API handles database errors gracefully"""
    
    # Mock database to raise error
    async def mock_fetch(*args):
        raise Exception("Database connection lost")
    
    monkeypatch.setattr("src.api.server.db_manager.fetch", mock_fetch)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/leads")
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    # Should NOT expose internal error details to client
    assert "Database connection lost" not in data["detail"]
```

**Run tests:**
```bash
# All API tests
pytest tests/test_api.py -v

# Single test
pytest tests/test_api.py::test_get_leads_success -v

# With coverage
pytest tests/test_api.py --cov=src.api
```

### Integration Tests (Full Stack)

**Test API → Database → Repository:**
```python
@pytest.mark.asyncio
async def test_call_initiation_updates_database():
    """Test call initiation creates call_log entry"""
    
    # Create test lead
    lead_repo = LeadRepository(db_manager)
    lead = await lead_repo.create_lead({
        "first_name": "Test",
        "last_name": "User",
        "phone": "+15551234567",
        # ... other fields
    })
    
    # Initiate call via API
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/calls/initiate",
            json={"lead_id": lead.id}
        )
    
    assert response.status_code == 200
    call_id = response.json()["call_id"]
    
    # Verify call_log entry created
    call_log_repo = CallLogRepository(db_manager)
    call_log = await call_log_repo.get_call_log_by_sid(call_id)
    
    assert call_log is not None
    assert call_log["lead_id"] == lead.id
    
    # Cleanup
    await lead_repo.delete_lead(lead.id)
```

### Test Fixtures (Shared Setup)

**conftest.py:**
```python
import pytest
from src.shared.database import DatabaseManager

@pytest.fixture(scope="session")
async def db_manager():
    """Shared database manager for tests"""
    manager = DatabaseManager(database_url=os.getenv("TEST_DATABASE_URL"))
    await manager.connect()
    yield manager
    await manager.close()

@pytest.fixture
async def test_lead_id(db_manager):
    """Create test lead, return ID, cleanup after test"""
    lead_repo = LeadRepository(db_manager)
    lead = await lead_repo.create_lead({
        "first_name": "Test",
        "last_name": "Lead",
        "phone": "+15551234567",
        "address": "123 Test St",
        "city": "Chicago",
        "county": "Cook",
        "state": "IL",
        "zip_code": "60601",
        "lead_type": "final_expense",
    })
    
    yield lead.id
    
    # Cleanup
    await lead_repo.delete_lead(lead.id)
```

### CI/CD Integration

**GitHub Actions (.github/workflows/test.yml):**
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql://postgres:test@localhost:5432/test
        run: pytest tests/test_api.py -v
```

### API Documentation

FastAPI auto-generates docs at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Use these to:
- Test endpoints interactively
- Share API contract with frontend team
- Verify request/response schemas

---

## 🔐 Environment Variables

**Required for API:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aidn

# LiveKit (for call dispatching)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

**Load in API:**
```python
from dotenv import load_dotenv
load_dotenv()

livekit_url = os.getenv("LIVEKIT_URL")
```

---

## 🚫 Common Pitfalls

### ❌ Don't Do This

1. **Blocking I/O in async functions**
   ```python
   async def get_data():
       time.sleep(1)  # ❌ Blocks entire event loop
   ```

2. **Raw SQL everywhere**
   ```python
   @app.post("/leads")
   async def create_lead(data: dict):
       await db.execute("INSERT INTO leads ...")  # ❌ Use repository
   ```

3. **No error handling**
   ```python
   @app.get("/leads/{lead_id}")
   async def get_lead(lead_id: str):
       lead = await repo.get(lead_id)  # ❌ What if not found?
       return lead
   ```

4. **Mixing business logic in endpoints**
   ```python
   @app.post("/calls/initiate")
   async def initiate_call(request: CallRequest):
       # ❌ 100 lines of call orchestration logic here
       # ✅ Move to service layer or repository
   ```

5. **Exposing internal errors**
   ```python
   except Exception as e:
       return {"error": str(e)}  # ❌ Leaks stack traces
   ```

### ✅ Do This Instead

1. **Use asyncio.sleep or async libraries**
   ```python
   async def get_data():
       await asyncio.sleep(1)  # ✅ Non-blocking
   ```

2. **Use repositories**
   ```python
   lead_repo = LeadRepository(db_manager)
   await lead_repo.create(lead_data)
   ```

3. **Always handle errors**
   ```python
   lead = await repo.get(lead_id)
   if not lead:
       raise HTTPException(status_code=404, detail="Lead not found")
   return lead
   ```

4. **Keep endpoints thin**
   ```python
   @app.post("/calls/initiate")
   async def initiate_call(request: CallRequest):
       call_service = CallService(db_manager, livekit_api)
       return await call_service.initiate_call(request)
   ```

5. **Log errors, return generic messages**
   ```python
   except Exception as e:
       logger.error(f"Call failed: {e}", exc_info=True)
       raise HTTPException(status_code=500, detail="Call initiation failed")
   ```

---

## 📊 Performance Considerations

### Database Connection Pooling

**Current:** Single DatabaseManager instance shared across requests
**Why:** Connection reuse, no per-request overhead

### Async Everything

**Current:** All endpoints use `async def`
**Why:** Non-blocking I/O for concurrent request handling

### Response Caching (Future)

**When to add:**
- `/leads` endpoint called frequently with same params
- Lead data doesn't change often

**How:**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@app.get("/leads")
@cache(expire=60)  # Cache for 60 seconds
async def get_leads():
    pass
```

---

## 🎯 API Development Checklist

When adding a new endpoint:

- [ ] Use `async def` for function
- [ ] Define Pydantic request model (if POST/PUT/PATCH)
- [ ] Define Pydantic response model
- [ ] Use repository pattern for database access
- [ ] Handle all error cases (400, 404, 500)
- [ ] Add type hints for all parameters
- [ ] Test with curl before dashboard integration
- [ ] Verify in Swagger UI docs
- [ ] Add logging for errors
- [ ] Update this reference doc if new patterns emerge

---

## 📚 Reference Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Pydantic Docs:** https://docs.pydantic.dev
- **Python Async:** https://docs.python.org/3/library/asyncio.html

---

*Reference Doc | API Development | Last Updated: January 27, 2026*
