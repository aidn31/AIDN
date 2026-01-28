# Monitoring & Observability Rules - AIDN

**Purpose:** Task-specific rules for monitoring production systems. Load this when setting up alerts, debugging issues, or tracking system health.

---

## 🎯 Monitoring Philosophy

**Core Principle:** You can't fix what you can't see.

**MVP Monitoring Goals:**
- Know when system is down within 5 minutes
- Track cost per call in real-time
- Identify performance degradation before users complain
- Debug production issues without guessing

---

## 🔧 Monitoring Stack

### Recommended Tools (MVP)

**Error Tracking:**
- **Tool:** Sentry (free tier: 5K events/month)
- **Why:** Automatic error capture, stack traces, user context
- **Setup:** 15 minutes, one SDK import

**Logging:**
- **Tool:** Railway logs (if using Railway) OR Papertrail
- **Why:** Free, searchable, real-time
- **Retention:** 7 days (MVP), 30 days (post-MVP)

**Metrics:**
- **Tool:** Custom dashboard (Next.js page) OR Grafana
- **Why:** Real-time KPIs visible at a glance
- **Update:** Every 5 seconds

**Uptime Monitoring:**
- **Tool:** UptimeRobot (free: 50 monitors)
- **Why:** External checks, alerts if down
- **Check:** Every 5 minutes

---

## 📊 Key Metrics to Track

### 1. Call Metrics (Most Important)

**Per Call:**
```python
{
  "call_id": "uuid",
  "lead_id": "uuid",
  "agent_id": "uuid",
  "started_at": "timestamp",
  "ended_at": "timestamp",
  "duration_seconds": 120,
  
  # Performance
  "latency_total_ms": 480,
  "latency_stt_ms": 120,
  "latency_llm_ms": 200,
  "latency_tts_ms": 80,
  "turn_count": 8,
  
  # Outcome
  "call_outcome": "booked",
  "appointment_booked": true,
  "calendar_event_created": true,
  
  # Costs
  "cost_stt": 0.008,
  "cost_llm": 0.0001,
  "cost_tts": 0.010,
  "cost_livekit": 0.010,
  "cost_total": 0.0281,
  
  # Errors (if any)
  "errors": [],
  "warnings": ["Calendar API slow response: 2.3s"]
}
```

**Aggregated Metrics (Dashboard):**
- **Calls today:** 47
- **Success rate:** 94% (44 successful, 3 failed)
- **Average duration:** 2m 15s
- **Booking rate:** 12% (5 appointments from 42 completed calls)
- **Average latency:** 485ms (target: <500ms)
- **Total cost today:** $1.32 ($0.028/call)

### 2. Voice Agent Health

**Real-time:**
- Active calls count (current)
- Queue depth (leads waiting to be called)
- Agent uptime (% time available)

**Per-component latency (P50, P95, P99):**
- STT latency
- LLM TTFT (time to first token)
- TTS TTFB (time to first byte)
- Total end-to-end

**Error rates:**
- LLM failures (timeouts, 429 rate limits)
- TTS failures
- Database connection errors
- Calendar API failures

### 3. Business Metrics

**Daily:**
- Appointments booked today
- Show rate (% of appointments where prospect was home)
- Conversion rate (calls → appointments)
- Cost per appointment
- Revenue impact (appointments × avg sale value)

**Weekly:**
- Total calls made
- Leads called vs remaining
- Top performing lead types
- Top performing counties
- Agent utilization (% of available time spent calling)

### 4. Infrastructure Metrics

**API Server:**
- Requests per minute
- Response time (P50, P95)
- Error rate (5xx errors)
- Memory usage
- CPU usage

**Database:**
- Active connections
- Query time (slow query log)
- Connection pool utilization
- Disk usage

**External Services:**
- LiveKit room count
- Groq API quota remaining
- Deepgram balance
- Cartesia credits

---

## 🚨 Alert Configuration

### Critical Alerts (Page Immediately)

**Voice Agent Down:**
```yaml
Condition: No calls started in last 10 minutes during calling hours
Action: Page on-call, SMS backup
Response: Restart agent, check logs
```

**Database Connection Lost:**
```yaml
Condition: 5 consecutive database errors
Action: Page on-call
Response: Check connection string, restart DB pool
```

**Payment Method Failure:**
```yaml
Condition: API returns 402 (payment required)
Action: Email + SMS to founder
Response: Update payment method immediately
```

### High Priority (Alert in 5 Minutes)

**Latency Spike:**
```yaml
Condition: P95 latency > 1000ms for 5 consecutive minutes
Action: Slack alert
Response: Check LLM provider status, switch to fallback if needed
```

**Booking Rate Drop:**
```yaml
Condition: Booking rate < 5% (50% below normal) over 20+ calls
Action: Slack alert
Response: Check prompt changes, review recent call logs
```

**Error Rate High:**
```yaml
Condition: Error rate > 10% over last 30 calls
Action: Slack alert
Response: Check error logs, identify common failure pattern
```

### Warning (Alert in 15 Minutes)

**Cost Budget:**
```yaml
Condition: Daily spend > $50 (MVP budget)
Action: Email notification
Response: Review if legitimate increase or runaway process
```

**Approaching Rate Limits:**
```yaml
Condition: Groq API at 80% of quota
Action: Slack notification
Response: Slow down calling or upgrade tier
```

**Low Lead Count:**
```yaml
Condition: < 50 fresh leads remaining for agent
Action: Dashboard notification
Response: Upload more leads
```

---

## 📝 Logging Strategy

### What to Log

**Every Call (MUST LOG):**
```python
logger.info(
    "Call completed",
    extra={
        "call_id": call_id,
        "lead_id": lead_id,
        "duration_seconds": duration,
        "outcome": outcome,
        "latency_total_ms": latency,
        "cost_total": cost,
        "errors_count": len(errors),
    }
)
```

**Every Turn in Conversation:**
```python
logger.debug(
    f"Turn {turn_num}",
    extra={
        "call_id": call_id,
        "stt_ms": stt_latency,
        "llm_ttft_ms": llm_latency,
        "tts_ttfb_ms": tts_latency,
        "user_input_length": len(user_text),
        "ai_response_length": len(ai_text),
    }
)
```

**Errors (Always Include Context):**
```python
logger.error(
    "LLM request failed",
    extra={
        "call_id": call_id,
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "error_type": type(e).__name__,
        "error_message": str(e),
        "retry_count": retry_count,
    },
    exc_info=True  # Include full stack trace
)
```

### Log Levels

**DEBUG:** Per-turn latency, RAG tool calls, minor events
**INFO:** Call started, call completed, appointment booked
**WARNING:** Slow response (>1s), fallback activated, calendar API failed
**ERROR:** LLM failed, database error, unexpected exception
**CRITICAL:** System-wide failure, payment method failed

### Searchable Fields

Make sure these are easily searchable:
- `call_id` - Find all logs for specific call
- `lead_id` - Track lead's calling history
- `agent_id` - Filter by human agent
- `error_type` - Group similar errors
- `outcome` - Filter by booking/no answer/etc.

---

## 🔍 Error Tracking with Sentry

### Setup

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",  # or "staging"
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
)
```

### What Sentry Automatically Captures

- Unhandled exceptions
- Stack traces
- User context (lead_id, agent_id)
- Breadcrumbs (recent events leading to error)
- Release version (git commit SHA)

### Add Context to Errors

```python
from sentry_sdk import set_context, set_tag

# At start of call
set_tag("call_id", call_id)
set_tag("lead_type", lead.lead_type)
set_context("lead", {
    "id": lead_id,
    "county": lead.county,
    "call_count": lead.call_count,
})

# Sentry will include this in error reports
```

### Alert on New Errors

**Sentry → Slack integration:**
- New error type → Immediate Slack message
- Spike in existing error → Alert if 10x normal rate
- Regression → Alert if error reappears after being resolved

---

## 📈 Custom Metrics Dashboard

### Build Simple Dashboard (Next.js Page)

**Location:** `web-dashboard/app/monitoring/page.tsx`

**Metrics to Display:**

```tsx
interface DashboardMetrics {
  // Real-time
  activeCalls: number;
  queueDepth: number;
  
  // Today
  callsToday: number;
  appointmentsToday: number;
  bookingRate: number;
  averageLatency: number;
  totalCost: number;
  
  // Last hour (for trend)
  callsLastHour: number;
  errorsLastHour: number;
  avgLatencyLastHour: number;
  
  // Alerts
  activeAlerts: Alert[];
}
```

**Auto-refresh every 5 seconds:**
```tsx
useEffect(() => {
  const interval = setInterval(fetchMetrics, 5000);
  return () => clearInterval(interval);
}, []);
```

**API Endpoint:**
```python
@app.get("/monitoring/metrics")
async def get_metrics():
    # Query database for today's stats
    # Return JSON with all metrics
    pass
```

---

## 🎯 Debugging Playbook

### Issue: Call Failed to Connect

**Check:**
1. LiveKit agent running? (`ps aux | grep main.py`)
2. Lead phone number valid? (Check format: +15551234567)
3. SIP trunk configured? (Check LIVEKIT_SIP_TRUNK_ID)
4. LiveKit Cloud account active? (Check billing)

**Debug:**
```bash
# Check agent logs
tail -f logs/voice-agent.log | grep ERROR

# Test SIP trunk
curl -X POST https://api.livekit.io/sip/... \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: High Latency (>1 second)

**Check:**
1. Is KV caching working? (Turn 2+ should be faster than Turn 1)
2. Groq API status? (Check status.groq.com)
3. Network latency? (Ping times to APIs)
4. Prompt size? (Should be <1500 tokens)

**Debug:**
```python
# Log per-component latency
logger.info(f"STT: {stt_ms}ms | LLM: {llm_ms}ms | TTS: {tts_ms}ms")

# Check if prompt is rebuilt every turn (BAD)
logger.debug(f"Prompt size: {len(prompt)} chars, {len(prompt)//4} tokens")
```

### Issue: Appointments Not Booking

**Check:**
1. Database connection OK?
2. `book_appointment()` stored procedure working?
3. Calendar API credentials valid?
4. Appointment slots available?

**Debug:**
```sql
-- Check available slots
SELECT * FROM appointment_slots 
WHERE agent_id = 'uuid' 
  AND status = 'available' 
  AND date >= CURRENT_DATE
LIMIT 10;

-- Check if booking is failing
SELECT * FROM call_logs 
WHERE outcome = 'booked' 
  AND started_at >= CURRENT_DATE;
```

### Issue: Cost Spike

**Check:**
1. Number of calls today (expected?)
2. Average call duration (unusually long?)
3. Failed calls retrying in loop?
4. Wrong API tier (using expensive model)?

**Debug:**
```python
# Calculate cost per call
total_cost = sum([call.cost_total for call in calls_today])
avg_cost = total_cost / len(calls_today)
logger.info(f"Avg cost/call: ${avg_cost:.4f} | Total: ${total_cost:.2f}")
```

---

## 📊 Weekly Review Checklist

Every Monday morning, review:

- [ ] Total calls last week vs goal
- [ ] Booking rate trend (improving or declining?)
- [ ] Average latency (meeting <500ms target?)
- [ ] Error rate (any new error patterns?)
- [ ] Cost per appointment (improving with volume?)
- [ ] Top 3 errors by frequency (prioritize fixes)
- [ ] Agent utilization (calling during scheduled hours?)
- [ ] Lead quality (which counties/types convert best?)

**Action Items:**
- If booking rate dropped → Review recent prompt changes
- If latency increased → Investigate LLM provider changes
- If errors spiked → Check external API status pages
- If cost increased → Review if due to volume or inefficiency

---

## 🚀 Setting Up Monitoring (Step-by-Step)

### Step 1: Sentry (15 minutes)

```bash
# Install
pip install sentry-sdk

# Add to .env
SENTRY_DSN=https://...@sentry.io/...

# Add to src/voice_agent/main.py (top of file)
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

### Step 2: Structured Logging (30 minutes)

```python
# src/shared/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, 'call_id'):
            log_obj['call_id'] = record.call_id
        if hasattr(record, 'lead_id'):
            log_obj['lead_id'] = record.lead_id
        return json.dumps(log_obj)

# Use in main.py
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Step 3: Metrics Tracking (1 hour)

```python
# src/shared/metrics.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CallMetrics:
    call_id: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    latency_total_ms: int
    latency_stt_ms: int
    latency_llm_ms: int
    latency_tts_ms: int
    cost_total: float
    outcome: str
    errors: list
    
    async def save(self, db_manager):
        """Save to call_logs table"""
        query = """
        INSERT INTO call_logs (
            id, started_at, ended_at, duration_seconds,
            latency_total_ms, cost_total, outcome
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await db_manager.execute(
            query, 
            self.call_id, self.started_at, self.ended_at,
            self.duration_seconds, self.latency_total_ms,
            self.cost_total, self.outcome
        )
```

### Step 4: Alerts (30 minutes)

```python
# src/shared/alerts.py
import requests
import os

def send_slack_alert(message: str, level: str = "warning"):
    """Send alert to Slack"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    color = {
        "info": "#36a64f",
        "warning": "#ff9900", 
        "error": "#ff0000",
        "critical": "#8B0000"
    }.get(level, "#808080")
    
    payload = {
        "attachments": [{
            "color": color,
            "title": f"AIDN Alert ({level.upper()})",
            "text": message,
            "ts": int(time.time())
        }]
    }
    
    requests.post(webhook_url, json=payload)

# Usage
if booking_rate < 0.05:
    send_slack_alert(
        f"⚠️ Booking rate dropped to {booking_rate:.1%} (expected 10%)",
        level="warning"
    )
```

---

## 🎯 Success Criteria

Monitoring is set up correctly when:

- [ ] You get alerted within 5 minutes if voice agent goes down
- [ ] You can see today's metrics (calls, bookings, cost) in under 30 seconds
- [ ] Every error includes call_id for quick debugging
- [ ] You know cost per call in real-time
- [ ] You get Slack alert when booking rate drops
- [ ] You can debug production issues without asking users "what happened?"

---

*Reference Doc | Monitoring | Last Updated: January 27, 2026*
