# Deployment & Infrastructure Rules - AIDN

**Purpose:** Task-specific rules for deploying AIDN to staging and production. Load this when setting up infrastructure, deploying changes, or handling incidents.

---

## 🎯 Deployment Philosophy

**Core Principles:**
- Never deploy directly to production
- Always test on staging first
- Make deployments reversible (rollback in 1 minute)
- Automate everything (reduce human error)

**MVP Goal:** Deploy with confidence in under 10 minutes.

---

## 🌍 Environment Strategy

### 1. Local Development

**Purpose:** Daily development work

```
API:       localhost:8000
Dashboard: localhost:3000
Database:  localhost:5432 (or Supabase dev project)
Voice:     Uses dev LiveKit project
```

**Database:** Local PostgreSQL OR Supabase development project

**External Services:** All use dev/test API keys
- LiveKit: Development project
- Groq: Development API key (lower rate limits)
- Deepgram: Sandbox project
- Cartesia: Test account

**Starting Services:**
```bash
# Terminal 1: Voice Agent
python -m src.voice_agent.main dev

# Terminal 2: API Server
uvicorn src.api.server:app --reload --port 8000

# Terminal 3: Dashboard
cd web-dashboard && npm run dev
```

---

### 2. Staging Environment

**Purpose:** Test before production, demo to investors/customers

```
API:       https://staging-api.aidn.io
Dashboard: https://staging.aidn.io
Database:  Supabase staging project (separate from prod)
Voice:     Uses prod LiveKit project (separate rooms)
```

**Database:** Copy of production schema, test data only

**External Services:** 
- LiveKit: Production project (rooms prefixed with `staging-`)
- Groq: Production API key (shared with prod, monitor usage)
- Deepgram: Production account
- Cartesia: Production account

**When to Use:**
- Before every production deploy
- Demo to investors/customers (not on real leads)
- Load testing
- Testing schema migrations

**Auto-Deploy:** Every push to `staging` branch

---

### 3. Production Environment

**Purpose:** Real customers, real calls, real money

```
API:       https://api.aidn.io
Dashboard: https://dashboard.aidn.io
Database:  Supabase production project
Voice:     Production LiveKit rooms
```

**Database:** Real data, daily backups enabled

**External Services:** All production API keys

**Manual Deploy:** Only after staging approval

**Monitoring:** Full monitoring stack (Sentry, logs, alerts)

---

## 🚀 Deployment Process

### Step-by-Step Checklist

#### Phase 1: Pre-Deploy (Local)

- [ ] All changes committed to git
- [ ] Tests pass locally (`pytest`)
- [ ] No lint errors (`ruff check`)
- [ ] Tested manually with real phone call
- [ ] Environment variables updated (if new variables added)
- [ ] Database migration ready (if schema changes)

#### Phase 2: Deploy to Staging

- [ ] Push to `staging` branch OR manually deploy
- [ ] Wait for CI to complete (GitHub Actions)
- [ ] Verify staging API is up: `curl https://staging-api.aidn.io/health`
- [ ] Verify staging dashboard loads
- [ ] Make test call on staging
- [ ] Check staging logs for errors
- [ ] Test new feature end-to-end

#### Phase 3: Deploy to Production

- [ ] Staging approval confirmed
- [ ] Notify team: "Deploying to production"
- [ ] Deploy to production (manual button click OR merge to `main`)
- [ ] Wait for deployment to complete (~2-5 minutes)
- [ ] **Smoke test production:**
  - [ ] API health check passes
  - [ ] Dashboard loads
  - [ ] Database connection works
  - [ ] Can fetch leads
  - [ ] (Optional) Make one test call if major voice changes
- [ ] Monitor for 15 minutes (watch error rate in Sentry)
- [ ] Announce: "Deploy complete, no issues"

#### Phase 4: Post-Deploy

- [ ] Update `docs/CHANGELOG.md` with what changed
- [ ] Close any related GitHub issues/PRs
- [ ] Tag release: `git tag v1.0.5 && git push --tags`

---

## 🔄 Rollback Process

### When to Rollback

**Immediately rollback if:**
- Error rate > 25% in first 5 minutes
- Critical feature completely broken
- Database corruption detected
- Can't make calls (voice agent down)

**Consider rollback if:**
- Error rate 10-25% (try quick fix first)
- New bug affects 25%+ of users
- Performance degrades significantly (latency 2x worse)

### How to Rollback (< 1 Minute)

**Option 1: Platform Rollback (Recommended)**

Most hosting platforms (Railway, Render, Fly.io) have one-click rollback:

```bash
# Railway
railway rollback

# Render
# Go to dashboard → Deploys → Click "Rollback" on previous version

# Fly.io
fly deploy --image registry.fly.io/aidn-api:v1.0.4
```

**Option 2: Git Rollback**

```bash
# Revert to last known good commit
git revert HEAD
git push

# OR reset to previous version
git reset --hard v1.0.4
git push --force

# CI will auto-deploy the reverted version
```

**Option 3: Feature Flag**

If you have feature flags, disable the problematic feature:

```python
# .env
FEATURE_NEW_BOOKING_FLOW=false
```

Restart services to pick up new env var.

### After Rollback

- [ ] Confirm error rate returns to normal
- [ ] Announce to team: "Rolled back, investigating"
- [ ] Create GitHub issue to track the bug
- [ ] Fix in development
- [ ] Deploy fix to staging
- [ ] Test thoroughly before re-deploying to production

---

## 🏗️ Infrastructure Setup

### Recommended Stack (MVP)

**Hosting:**
- **API + Voice Agent:** Railway ($5/month) OR Render ($7/month)
- **Dashboard:** Vercel (free for preview, $20/month pro)
- **Database:** Supabase (free tier, then $25/month)

**Why these?**
- Easy deployment (git push = deploy)
- Built-in CI/CD
- One-click rollback
- Affordable for MVP
- Scale-ready (can handle 100+ concurrent calls)

### Alternative Stack (Post-MVP)

**If you outgrow Railway/Render:**
- **API + Voice:** AWS ECS / Kubernetes
- **Dashboard:** Vercel or Cloudflare Pages
- **Database:** AWS RDS PostgreSQL
- **CDN:** Cloudflare

---

## 📦 Database Migrations

### Migration Strategy

**Rule:** Never modify production database schema directly.

**Process:**
1. Create migration file locally
2. Test on local database
3. Deploy to staging database first
4. Test on staging for 24 hours
5. Deploy to production during low-traffic window

### Migration File Example

**Location:** `src/shared/database/migrations/005_add_cost_tracking.sql`

```sql
-- Migration: Add cost tracking to call_logs
-- Date: 2026-01-27
-- Author: Tommy

BEGIN;

-- Add cost columns
ALTER TABLE call_logs 
ADD COLUMN cost_stt DECIMAL(10, 4) DEFAULT 0,
ADD COLUMN cost_llm DECIMAL(10, 4) DEFAULT 0,
ADD COLUMN cost_tts DECIMAL(10, 4) DEFAULT 0,
ADD COLUMN cost_livekit DECIMAL(10, 4) DEFAULT 0,
ADD COLUMN cost_total DECIMAL(10, 4) DEFAULT 0;

-- Add index for cost queries
CREATE INDEX idx_call_logs_cost_total ON call_logs(cost_total);

COMMIT;
```

### Running Migrations

**Locally:**
```bash
psql $DATABASE_URL < src/shared/database/migrations/005_add_cost_tracking.sql
```

**Staging:**
```bash
# Via Supabase dashboard SQL editor
# OR via CLI
psql $STAGING_DATABASE_URL < src/shared/database/migrations/005_add_cost_tracking.sql
```

**Production:**
```bash
# During maintenance window (or off-peak hours)
# Announce downtime if needed (usually <1 minute for simple ALTER)
psql $PROD_DATABASE_URL < src/shared/database/migrations/005_add_cost_tracking.sql
```

### Reversible Migrations

Always create a rollback migration:

**005_add_cost_tracking_rollback.sql:**
```sql
BEGIN;

DROP INDEX IF EXISTS idx_call_logs_cost_total;

ALTER TABLE call_logs 
DROP COLUMN IF EXISTS cost_stt,
DROP COLUMN IF EXISTS cost_llm,
DROP COLUMN IF EXISTS cost_tts,
DROP COLUMN IF EXISTS cost_livekit,
DROP COLUMN IF EXISTS cost_total;

COMMIT;
```

---

## 🔐 Environment Variables

### Managing Secrets

**❌ Never commit:**
- API keys
- Database passwords
- Secret tokens
- `.env` file

**✅ Always commit:**
- `.env.example` (with placeholder values)

### Environment Variable Checklist

**Before deploying to new environment:**

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all values
- [ ] Test locally first
- [ ] Add to hosting platform's environment variables
- [ ] Restart services to pick up new variables

### Required Variables per Environment

**Local (.env):**
```bash
DATABASE_URL=postgresql://localhost:5432/aidn_dev
GROQ_API_KEY=gsk_test_...
DEEPGRAM_API_KEY=test_...
CARTESIA_API_KEY=test_...
LIVEKIT_URL=wss://your-dev-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

**Staging:**
```bash
DATABASE_URL=postgresql://...supabase.co:5432/postgres
GROQ_API_KEY=gsk_prod_...  # Production key, monitor usage
SENTRY_DSN=https://...@sentry.io/staging
ENVIRONMENT=staging
```

**Production:**
```bash
DATABASE_URL=postgresql://...supabase.co:5432/postgres
GROQ_API_KEY=gsk_prod_...
SENTRY_DSN=https://...@sentry.io/production
ENVIRONMENT=production
SLACK_WEBHOOK_URL=https://hooks.slack.com/... # For alerts
```

---

## 🚨 Incident Response

### Severity Levels

**P0 (Critical) - Respond within 5 minutes:**
- Voice agent completely down (can't make any calls)
- Database down (no reads/writes)
- Dashboard completely inaccessible
- Payment failure (can't charge customers)

**P1 (High) - Respond within 30 minutes:**
- High error rate (>25%)
- Severe performance degradation (latency 3x normal)
- One major feature broken (e.g., booking doesn't work)

**P2 (Medium) - Respond within 2 hours:**
- Moderate error rate (10-25%)
- Minor feature broken
- Performance degraded (latency 2x normal)

**P3 (Low) - Respond within 24 hours:**
- Single user affected
- Cosmetic issue
- Non-critical feature

### Incident Process

1. **Detect:** Alert fires (Sentry, uptime monitor, customer report)
2. **Acknowledge:** Confirm you're investigating
3. **Diagnose:** Check logs, metrics, external service status
4. **Mitigate:** Fix immediately if possible, otherwise rollback
5. **Resolve:** Deploy fix, verify error rate returns to normal
6. **Post-Mortem:** Write up what happened, how to prevent

### On-Call Rotation (When Team Grows)

**For now (solo founder):**
- You're always on-call
- Set up phone alerts for P0/P1 issues
- Have laptop ready to debug/rollback

**Future (with team):**
- Rotate weekly
- On-call person gets pager alerts
- Off-call people can sleep peacefully

---

## 🧪 CI/CD Pipeline

### GitHub Actions Workflow

**On every push:**
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
      - name: Lint
        run: ruff check .
```

**On push to `staging` branch:**
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway (Staging)
        run: |
          curl -X POST $RAILWAY_WEBHOOK_URL_STAGING
```

**On push to `main` branch (Production):**
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests first
        run: pytest
      - name: Deploy to Railway (Production)
        run: |
          curl -X POST $RAILWAY_WEBHOOK_URL_PROD
      - name: Notify Slack
        run: |
          curl -X POST $SLACK_WEBHOOK \
            -d '{"text": "🚀 Deployed to production!"}'
```

---

## 📊 Deployment Metrics

### Track These per Deploy

```json
{
  "deploy_id": "d123",
  "deployed_at": "2026-01-27T10:30:00Z",
  "deployed_by": "tommy",
  "environment": "production",
  "git_commit": "abc123",
  "git_tag": "v1.0.5",
  
  "duration_seconds": 180,
  "rollback_required": false,
  
  "changes": {
    "files_changed": 5,
    "lines_added": 120,
    "lines_removed": 45
  },
  
  "post_deploy_health": {
    "error_rate_5min": 0.02,  # 2%
    "latency_p95_5min": 480,
    "successful_calls_5min": 3
  }
}
```

### Success Criteria

Deploy is successful if after 15 minutes:
- [ ] Error rate < 5% (same as pre-deploy)
- [ ] Latency P95 < 700ms (not significantly worse)
- [ ] At least 3 successful calls made
- [ ] No critical errors in Sentry
- [ ] Dashboard loads without errors

---

## 🎯 Deployment Checklist (Quick Reference)

**Pre-Deploy:**
- [ ] Tests pass
- [ ] Feature tested locally
- [ ] Environment variables ready
- [ ] Database migration tested (if applicable)

**Deploy to Staging:**
- [ ] Push to staging
- [ ] Verify deployment succeeded
- [ ] Smoke test
- [ ] Check logs

**Deploy to Production:**
- [ ] Staging approved
- [ ] Notify team
- [ ] Deploy
- [ ] Smoke test immediately
- [ ] Monitor for 15 minutes
- [ ] Update changelog

**If Issues:**
- [ ] Rollback if error rate >25%
- [ ] Fix and redeploy to staging first
- [ ] Don't deploy to prod until staging is stable for 24h

---

## 🚀 Quick Start: Setting Up Deployment

### Step 1: Choose Hosting (15 minutes)

**Recommended: Railway**
1. Sign up at railway.app
2. Connect GitHub repo
3. Add project (API)
4. Add environment variables
5. Deploy

**Dashboard on Vercel:**
1. Sign up at vercel.com
2. Import GitHub repo (`web-dashboard` folder)
3. Auto-deploys on push

### Step 2: Set Up Staging (30 minutes)

1. Create `staging` branch in git
2. Deploy to Railway staging project
3. Set `ENVIRONMENT=staging` in env vars
4. Test thoroughly

### Step 3: Set Up CI/CD (30 minutes)

1. Create `.github/workflows/test.yml`
2. Create `.github/workflows/deploy-staging.yml`
3. Create `.github/workflows/deploy-production.yml`
4. Test: Push to staging, verify auto-deploy

### Step 4: Document (15 minutes)

1. Update README with deployment instructions
2. Add "How to Rollback" section
3. List all environment variables needed

---

*Reference Doc | Deployment | Last Updated: January 27, 2026*
