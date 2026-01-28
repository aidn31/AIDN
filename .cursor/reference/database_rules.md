# Database Rules - AIDN

**Purpose:** Task-specific rules for working with AIDN PostgreSQL database. Load this when modifying schema, creating migrations, or working with repositories.

---

## 🏗️ Database Architecture

**Database:** PostgreSQL with `asyncpg` driver
**Connection:** Pool-based (2-10 connections)
**Pattern:** Repository pattern (no raw SQL in API/business logic)

```
Application Layer
        ↓
Repository Layer (LeadRepository, AgentRepository, etc.)
        ↓
DatabaseManager (connection pool)
        ↓
PostgreSQL Database
```

---

## 📊 Database Schema

### Core Tables

#### 1. `leads` - Lead Management
```sql
- id (UUID, PK)
- first_name, last_name, phone, address
- city, county, state, zip_code
- lead_type (final_expense, term_life, whole_life, mortgage_protection)
- lead_source
- agent_id (FK to agent_profiles)
- created_at, uploaded_at
- last_called_at, next_call_at, call_count
- call_outcome (fresh, no_answer, not_interested, booked, callback, disconnected, wrong_number, dnc)
- is_active (soft delete)
```

**Lead Lifecycle States:**
- `fresh` - Never called
- `no_answer` - Called but no answer
- `callback` - Requested callback
- `not_interested` - Declined
- `booked` - Appointment scheduled
- `disconnected` - Number out of service
- `wrong_number` - Wrong person
- `dnc` - Do not call

#### 2. `agent_profiles` - Human Agents
```sql
- id (UUID, PK)
- agent_name, phone, email
- physical_description, car_description
- google_calendar_id
- earliest_appointment_time, latest_appointment_time
- slot_gap_hours (time between appointments)
- is_active
- created_at, updated_at
```

#### 3. `agent_availability` - Agent Schedules
```sql
- id (UUID, PK)
- agent_id (FK)
- day_of_week (0-6, 0=Sunday)
- is_available
- calling_start_time, calling_end_time
- max_appointments
- first_appointment_time
```

**UNIQUE constraint:** `(agent_id, day_of_week)`

#### 4. `agent_territories` - Geographic Assignments
```sql
- id (UUID, PK)
- agent_id (FK)
- county, state, zip_code
- lead_types (array of strings)
```

#### 5. `appointment_slots` - Booking System
```sql
- id (UUID, PK)
- agent_id (FK)
- date, time
- status (available, booked, completed, no_show, cancelled)
- lead_id (FK)
- booked_at
- created_at
```

**UNIQUE constraint:** `(agent_id, date, time)` - Prevents double-booking

#### 6. `call_logs` - Call History
```sql
- id (UUID, PK)
- lead_id (FK), agent_id (FK)
- call_sid (Twilio identifier)
- started_at, ended_at, duration_seconds
- outcome
- recording_url, transcript, notes
```

---

## 🔗 Indexes for Performance

**Current Indexes:**
```sql
-- Leads (most frequently queried table)
idx_leads_agent_id          -- Filter by agent
idx_leads_call_outcome      -- Filter by outcome (fresh, no_answer, etc.)
idx_leads_next_call_at      -- Find leads ready to call
idx_leads_county_state      -- Geographic filtering

-- Appointment Slots
idx_appointment_slots_agent_date  -- Agent daily schedule
idx_appointment_slots_status      -- Find available slots

-- Call Logs
idx_call_logs_lead_id       -- Lead call history
idx_call_logs_started_at    -- Chronological queries
```

**Why These Indexes:**
- `next_call_at` - Used in call queue logic
- `county, state` - Territory-based lead routing
- `agent_id` - Most queries filter by agent

---

## 🔒 Foreign Key Constraints

**All relationships enforced at database level:**
```sql
leads.agent_id          → agent_profiles.id
agent_availability.agent_id → agent_profiles.id
agent_territories.agent_id  → agent_profiles.id
appointment_slots.agent_id  → agent_profiles.id
appointment_slots.lead_id   → leads.id
call_logs.lead_id          → leads.id
call_logs.agent_id         → agent_profiles.id
```

**Benefits:**
- Data integrity guaranteed
- Cascading behavior controlled
- Can't orphan records

---

## 🛠️ Repository Pattern (MANDATORY)

### ✅ Always Use Repositories

**Pattern:**
```python
from ..shared.database import DatabaseManager, LeadRepository

# Initialize
db_manager = DatabaseManager()
await db_manager.connect()

# Use repository
lead_repo = LeadRepository(db_manager)
lead = await lead_repo.get_lead_by_id(lead_id)
```

### Current Repositories

**LeadRepository:**
- `get_lead_by_id(lead_id)` - Get single lead
- `get_leads_for_calling(agent_id, limit)` - Get leads ready to call (prioritized)
- `update_lead_outcome(lead_id, outcome, next_call_at)` - Update after call
- `create_lead(lead_data)` - Insert new lead

**AgentRepository:**
- `get_agent_by_id(agent_id)` - Get agent profile
- `get_active_agents()` - List all active agents
- `is_agent_available_for_calling(agent_id)` - Check if agent can call now
- `get_agent_daily_appointment_limit(agent_id)` - Max appointments today

**AppointmentRepository:**
- `get_available_slots(agent_id, start_date, end_date)` - Find open slots
- `book_slot(slot_id, lead_id)` - **Atomic booking** (uses stored procedure)
- `get_agent_appointments_today(agent_id)` - Count of today's appointments
- `generate_slots_for_agent(agent_id, start_date, end_date)` - Create slots

**CallLogRepository:**
- `create_call_log(call_data)` - Log new call
- `update_call_log(call_id, update_data)` - Update call details
- `get_call_logs_for_lead(lead_id)` - Lead call history
- `get_call_logs_by_sid(call_sid)` - Find by Twilio SID

---

## 🔄 Connection Management

### Connection Pool

**Configuration:**
```python
self.pool = await asyncpg.create_pool(
    self.database_url,
    min_size=2,    # Minimum connections
    max_size=10,   # Maximum connections
    command_timeout=60  # Query timeout (seconds)
)
```

**Why Connection Pooling:**
- Reuse connections across requests
- No overhead of creating new connection per query
- Handles concurrent requests efficiently

### DatabaseManager Methods

**execute(query, *args)** - No return value (INSERT, UPDATE, DELETE)
```python
result = await db.execute("UPDATE leads SET is_active = $1 WHERE id = $2", False, lead_id)
```

**fetch(query, *args)** - Multiple rows
```python
rows = await db.fetch("SELECT * FROM leads WHERE is_active = true")
```

**fetchrow(query, *args)** - Single row
```python
row = await db.fetchrow("SELECT * FROM leads WHERE id = $1", lead_id)
```

**fetchval(query, *args)** - Single value
```python
count = await db.fetchval("SELECT COUNT(*) FROM leads")
```

---

## 🗄️ Stored Procedures

### 1. `book_appointment()` - Atomic Booking

**Purpose:** Prevent double-booking via database-level locking

**Usage:**
```python
query = "SELECT success, slot_id FROM book_appointment($1, $2)"
result = await db.fetchrow(query, slot_id, lead_id)

if result['success']:
    print("Booking successful!")
else:
    print("Slot already booked")
```

**How It Works:**
```sql
UPDATE appointment_slots
SET status = 'booked', lead_id = p_lead_id, booked_at = NOW()
WHERE id = p_slot_id AND status = 'available';

IF FOUND THEN
    RETURN true;
ELSE
    RETURN false;  -- Slot was already booked
END IF;
```

**Critical:** This is the ONLY way to book appointments safely in concurrent environment.

### 2. `generate_appointment_slots()` - Bulk Slot Creation

**Purpose:** Create appointment slots based on agent availability

**Usage:**
```python
query = "SELECT generate_appointment_slots($1, $2, $3)"
slots_created = await db.fetchval(query, agent_id, start_date, end_date)
print(f"Created {slots_created} slots")
```

**Logic:**
1. Iterate through date range
2. Check agent availability for day of week
3. Generate slots based on `max_appointments` and `slot_gap_hours`
4. Skip if slot already exists (idempotent)

---

## ✅ Common Query Patterns

### Get Leads Ready to Call (Prioritized)

```python
query = """
SELECT * FROM leads
WHERE agent_id = $1
  AND is_active = true
  AND call_outcome IN ('fresh', 'no_answer', 'callback')
  AND (next_call_at IS NULL OR next_call_at <= NOW())
ORDER BY
  CASE call_outcome
    WHEN 'fresh' THEN 1      -- Highest priority
    WHEN 'callback' THEN 2   -- Requested callback
    WHEN 'no_answer' THEN 3  -- Retry
  END,
  created_at ASC             -- Oldest first within priority
LIMIT $2
"""
```

**Priority Order:**
1. Fresh leads (never called)
2. Callbacks (specific time requested)
3. No answers (retry)

### Check Agent Availability

```python
query = """
SELECT av.is_available, av.calling_start_time, av.calling_end_time
FROM agent_availability av
WHERE av.agent_id = $1
  AND av.day_of_week = EXTRACT(DOW FROM NOW())
  AND av.is_available = true
  AND NOW()::time BETWEEN av.calling_start_time AND av.calling_end_time
"""
```

Uses PostgreSQL `EXTRACT(DOW FROM NOW())` to get current day of week.

### Update Lead After Call

```python
query = """
UPDATE leads
SET call_outcome = $2,
    last_called_at = NOW(),
    call_count = call_count + 1,
    next_call_at = $3
WHERE id = $1
"""
await db.execute(query, lead_id, "no_answer", next_retry_time)
```

---

## 🚫 Common Pitfalls

### ❌ Don't Do This

1. **Raw SQL in API endpoints**
   ```python
   # ❌ Bad
   @app.get("/leads")
   async def get_leads():
       rows = await db.fetch("SELECT * FROM leads")
       return rows
   ```

2. **Forget to use await**
   ```python
   # ❌ Bad
   lead = lead_repo.get_lead_by_id(lead_id)  # Missing await
   ```

3. **Not handling None returns**
   ```python
   # ❌ Bad
   lead = await lead_repo.get_lead_by_id(lead_id)
   print(lead.first_name)  # Crashes if lead is None
   ```

4. **Manual booking (race condition)**
   ```python
   # ❌ Bad - not atomic
   slot = await get_slot(slot_id)
   if slot.status == 'available':
       await update_slot(slot_id, 'booked')  # Another request could book in between!
   ```

5. **Not using indexes**
   ```sql
   -- ❌ Bad - full table scan
   SELECT * FROM leads WHERE phone = '+15551234567'  -- No index on phone
   ```

### ✅ Do This Instead

1. **Use repositories**
   ```python
   lead_repo = LeadRepository(db_manager)
   leads = await lead_repo.get_leads_for_calling(agent_id, limit=10)
   ```

2. **Always await async functions**
   ```python
   lead = await lead_repo.get_lead_by_id(lead_id)
   ```

3. **Handle None**
   ```python
   lead = await lead_repo.get_lead_by_id(lead_id)
   if not lead:
       raise HTTPException(status_code=404, detail="Lead not found")
   print(lead.first_name)
   ```

4. **Use stored procedure for booking**
   ```python
   success = await appointment_repo.book_slot(slot_id, lead_id)
   ```

5. **Add index if needed**
   ```sql
   CREATE INDEX idx_leads_phone ON leads(phone);
   ```

---

## 📝 Migration Workflow

### Creating a Migration

**Step 1:** Create migration file
```bash
touch src/shared/database/migrations/001_add_email_to_leads.sql
```

**Step 2:** Write migration
```sql
-- Add column
ALTER TABLE leads ADD COLUMN email VARCHAR(255);

-- Add index if needed
CREATE INDEX idx_leads_email ON leads(email);
```

**Step 3:** Apply migration
```python
# In migration.py
async def apply_migration(db_manager, migration_file):
    with open(migration_file, 'r') as f:
        sql = f.read()
    await db_manager.execute(sql)
```

### Migration Best Practices

**DO:**
- ✅ Make migrations idempotent (safe to run multiple times)
- ✅ Add indexes in separate step from column creation
- ✅ Use `IF NOT EXISTS` for new tables/indexes
- ✅ Test on local database first
- ✅ Backup production before running

**DON'T:**
- ❌ Modify existing migrations (create new one)
- ❌ Delete data without backup
- ❌ Run migrations during peak hours
- ❌ Make breaking changes without rollback plan

---

## 🔐 Data Integrity Rules

### 1. Soft Deletes

**Never hard delete leads or agents:**
```sql
-- ✅ Good
UPDATE leads SET is_active = false WHERE id = $1;

-- ❌ Bad
DELETE FROM leads WHERE id = $1;
```

**Why:** Preserve call history, analytics, compliance records.

### 2. UUID Primary Keys

**All tables use UUIDs:**
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
```

**Why:**
- Globally unique (safe for distributed systems)
- No integer overflow
- Harder to enumerate/guess

### 3. CHECK Constraints

**Enforce valid values at database level:**
```sql
lead_type VARCHAR(50) CHECK (lead_type IN ('final_expense', 'term_life', 'whole_life', 'mortgage_protection'))
call_outcome VARCHAR(50) CHECK (call_outcome IN ('fresh', 'no_answer', 'not_interested', 'booked', 'callback', 'disconnected', 'wrong_number', 'dnc'))
```

**Why:** Invalid data can't be inserted, even if application bug.

### 4. Foreign Key Cascades

**Default behavior: RESTRICT**
```sql
FOREIGN KEY (agent_id) REFERENCES agent_profiles(id)
```

**Means:** Can't delete agent if they have leads.

**To allow cascading (use carefully):**
```sql
FOREIGN KEY (agent_id) REFERENCES agent_profiles(id) ON DELETE CASCADE
```

---

## 🧪 Testing Database Changes

### 3 Levels of Testing

1. **Query Testing** - Test SQL queries in psql (fast iteration)
2. **Repository Testing** - Test Python methods with test database
3. **Integration Testing** - Test full API → Repository → Database flow

### Query Testing (psql)

**Before adding to repository:**
```bash
psql $DATABASE_URL

# Test query
SELECT * FROM leads WHERE call_outcome = 'fresh' LIMIT 5;

# Check execution plan
EXPLAIN ANALYZE SELECT * FROM leads WHERE county = 'Cook';
```

### Verify Indexes Are Used

```sql
EXPLAIN ANALYZE
SELECT * FROM leads WHERE county = 'Cook';

-- Look for "Index Scan" not "Seq Scan"
-- Example output:
-- Index Scan using idx_leads_county_state on leads  (cost=0.29..8.31 rows=1 width=...)
```

### Repository Unit Tests

**Location:** `tests/test_database.py`

**Test LeadRepository:**
```python
import pytest
from src.shared.database import DatabaseManager, LeadRepository

@pytest.mark.asyncio
async def test_create_lead(db_manager):
    """Test creating a lead"""
    lead_repo = LeadRepository(db_manager)
    
    lead_data = {
        "first_name": "John",
        "last_name": "Smith",
        "phone": "+15551234567",
        "address": "123 Oak St",
        "city": "Chicago",
        "county": "Cook",
        "state": "IL",
        "zip_code": "60601",
        "lead_type": "final_expense",
        "agent_id": "test-agent-uuid",
    }
    
    lead = await lead_repo.create_lead(lead_data)
    
    assert lead is not None
    assert lead["first_name"] == "John"
    assert lead["phone"] == "+15551234567"
    assert lead["is_active"] is True
    
    # Cleanup
    await lead_repo.delete_lead(lead["id"])

@pytest.mark.asyncio
async def test_get_lead_by_id(db_manager, test_lead_id):
    """Test fetching lead by ID"""
    lead_repo = LeadRepository(db_manager)
    
    lead = await lead_repo.get_lead_by_id(test_lead_id)
    
    assert lead is not None
    assert lead["id"] == test_lead_id

@pytest.mark.asyncio
async def test_get_lead_by_id_not_found(db_manager):
    """Test 404 case - lead doesn't exist"""
    lead_repo = LeadRepository(db_manager)
    
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    lead = await lead_repo.get_lead_by_id(fake_uuid)
    
    assert lead is None

@pytest.mark.asyncio
async def test_update_lead_outcome(db_manager, test_lead_id):
    """Test updating lead after call"""
    lead_repo = LeadRepository(db_manager)
    
    # Update outcome
    await lead_repo.update_lead_outcome(
        test_lead_id,
        outcome="no_answer",
        next_call_at=datetime.now() + timedelta(hours=2)
    )
    
    # Verify update
    lead = await lead_repo.get_lead_by_id(test_lead_id)
    assert lead["call_outcome"] == "no_answer"
    assert lead["call_count"] == 1  # Should increment
    assert lead["next_call_at"] is not None
```

**Test AppointmentRepository:**
```python
@pytest.mark.asyncio
async def test_book_appointment_atomic(db_manager, test_slot_id, test_lead_id):
    """Test atomic appointment booking (prevents double-booking)"""
    appt_repo = AppointmentRepository(db_manager)
    
    # Book slot
    success = await appt_repo.book_slot(test_slot_id, test_lead_id)
    assert success is True
    
    # Try to book same slot again (should fail)
    success2 = await appt_repo.book_slot(test_slot_id, "different-lead-id")
    assert success2 is False  # Slot already booked

@pytest.mark.asyncio
async def test_get_available_slots(db_manager, test_agent_id):
    """Test fetching available appointment slots"""
    appt_repo = AppointmentRepository(db_manager)
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=2)
    
    slots = await appt_repo.get_available_slots(
        test_agent_id,
        start_date,
        end_date
    )
    
    assert isinstance(slots, list)
    # All returned slots should be 'available'
    for slot in slots:
        assert slot["status"] == "available"
        assert slot["agent_id"] == test_agent_id
```

**Test CallLogRepository:**
```python
@pytest.mark.asyncio
async def test_create_call_log(db_manager, test_lead_id):
    """Test logging a call"""
    call_repo = CallLogRepository(db_manager)
    
    call_data = {
        "lead_id": test_lead_id,
        "agent_id": "test-agent-uuid",
        "call_sid": "test-call-123",
        "started_at": datetime.now(),
        "duration_seconds": 120,
        "outcome": "booked",
        "cost_total": 0.035,
    }
    
    call_log = await call_repo.create_call_log(call_data)
    
    assert call_log is not None
    assert call_log["lead_id"] == test_lead_id
    assert call_log["outcome"] == "booked"
    
    # Cleanup
    await call_repo.delete_call_log(call_log["id"])
```

### Test Database Constraints

**Test foreign key constraints:**
```python
@pytest.mark.asyncio
async def test_foreign_key_constraint(db_manager):
    """Test that invalid agent_id is rejected"""
    lead_repo = LeadRepository(db_manager)
    
    lead_data = {
        "first_name": "Test",
        "agent_id": "invalid-uuid-not-in-agents-table",
        # ... other fields
    }
    
    with pytest.raises(Exception) as exc_info:
        await lead_repo.create_lead(lead_data)
    
    assert "foreign key constraint" in str(exc_info.value).lower()
```

**Test CHECK constraints:**
```python
@pytest.mark.asyncio
async def test_invalid_lead_type_rejected(db_manager):
    """Test that invalid lead_type is rejected by CHECK constraint"""
    lead_repo = LeadRepository(db_manager)
    
    lead_data = {
        "first_name": "Test",
        "lead_type": "invalid_type",  # Not in allowed values
        # ... other fields
    }
    
    with pytest.raises(Exception) as exc_info:
        await lead_repo.create_lead(lead_data)
    
    assert "check constraint" in str(exc_info.value).lower()
```

### Test Database Transactions

**Test rollback on error:**
```python
@pytest.mark.asyncio
async def test_transaction_rollback(db_manager):
    """Test that failed transaction rolls back changes"""
    
    async with db_manager.pool.acquire() as conn:
        async with conn.transaction():
            # Insert lead
            lead_id = await conn.fetchval(
                "INSERT INTO leads (...) VALUES (...) RETURNING id"
            )
            
            # Verify lead exists within transaction
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM leads WHERE id = $1", lead_id
            )
            assert count == 1
            
            # Force rollback by raising exception
            raise Exception("Intentional rollback")
    
    # Verify lead was NOT committed (rollback worked)
    count = await db_manager.fetchval(
        "SELECT COUNT(*) FROM leads WHERE id = $1", lead_id
    )
    assert count == 0
```

### Test Stored Procedures

**Test book_appointment() procedure:**
```python
@pytest.mark.asyncio
async def test_book_appointment_procedure(db_manager, test_slot_id, test_lead_id):
    """Test book_appointment stored procedure"""
    
    # Call stored procedure
    result = await db_manager.fetchrow(
        "SELECT success, slot_id FROM book_appointment($1, $2)",
        test_slot_id,
        test_lead_id
    )
    
    assert result["success"] is True
    assert result["slot_id"] == test_slot_id
    
    # Verify slot is now booked
    slot = await db_manager.fetchrow(
        "SELECT * FROM appointment_slots WHERE id = $1",
        test_slot_id
    )
    assert slot["status"] == "booked"
    assert slot["lead_id"] == test_lead_id
```

### Test Fixtures (Shared Test Data)

**conftest.py:**
```python
import pytest
import os
from datetime import datetime, timedelta
from src.shared.database import DatabaseManager, LeadRepository, AppointmentRepository

@pytest.fixture(scope="session")
async def db_manager():
    """Test database connection"""
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        pytest.skip("TEST_DATABASE_URL not set")
    
    manager = DatabaseManager(test_db_url)
    await manager.connect()
    
    yield manager
    
    await manager.close()

@pytest.fixture
async def test_lead_id(db_manager):
    """Create test lead, return ID, cleanup after"""
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
        "agent_id": "test-agent-uuid",
    })
    
    yield lead["id"]
    
    # Cleanup
    await db_manager.execute("DELETE FROM leads WHERE id = $1", lead["id"])

@pytest.fixture
async def test_slot_id(db_manager, test_agent_id):
    """Create test appointment slot"""
    slot_id = await db_manager.fetchval("""
        INSERT INTO appointment_slots (agent_id, date, time, status)
        VALUES ($1, $2, $3, 'available')
        RETURNING id
    """, test_agent_id, datetime.now().date(), "10:00")
    
    yield slot_id
    
    # Cleanup
    await db_manager.execute("DELETE FROM appointment_slots WHERE id = $1", slot_id)
```

### Run Tests

```bash
# All database tests
pytest tests/test_database.py -v

# Single test
pytest tests/test_database.py::test_create_lead -v

# With coverage
pytest tests/test_database.py --cov=src.shared.database

# Run against test database
TEST_DATABASE_URL=postgresql://localhost:5432/aidn_test pytest tests/test_database.py
```

---

## 📊 Performance Monitoring

### Slow Query Log

**Enable in PostgreSQL:**
```sql
SET log_min_duration_statement = 1000;  -- Log queries > 1 second
```

### Connection Pool Stats

**Monitor in application:**
```python
logger.info(f"Pool size: {db.pool.get_size()}")
logger.info(f"Pool max size: {db.pool.get_max_size()}")
```

---

## 🎯 Database Development Checklist

When modifying database:

- [ ] Use repository pattern (no raw SQL in API)
- [ ] Always use `await` for async database calls
- [ ] Handle `None` returns from queries
- [ ] Use stored procedures for atomic operations (booking)
- [ ] Add indexes for frequently queried columns
- [ ] Use CHECK constraints for enum-like fields
- [ ] Soft delete with `is_active = false`
- [ ] Test queries locally before deploying
- [ ] Create migration file for schema changes
- [ ] Update this reference doc if new patterns emerge

---

*Reference Doc | Database | Last Updated: January 27, 2026*
