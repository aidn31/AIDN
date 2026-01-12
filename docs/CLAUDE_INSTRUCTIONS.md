# Claude Instructions for AIDN Project

## 🚀 When Starting a New Chat

When Tommy says "Read docs and continue" or starts a new chat, do this:

### Step 1: Read These Files (In Order)
1. `AIDN_SPECIFICATION.md` - Understand what we're building and why
2. `docs/PROJECT_STATUS.md` - Understand where we are now
3. `docs/NEXT_STEPS.md` - Know what to do next
4. `docs/ISSUES_RESOLVED.md` - Don't re-solve solved problems
5. `docs/DECISION_LOG.md` - Understand why we made certain choices
6. `docs/ARCHITECTURE.md` - Understand technical decisions

### Step 2: Confirm Understanding
Provide a brief summary:
- "AIDN is: [one sentence]"
- "Current phase: PROTOTYPE / PRODUCT"
- "Current status: [what's working, what's not]"
- "Next priority: [the #1 task]"
- "Any blockers: [yes/no, what]"

### Step 3: Ask Before Proceeding
- "Does this look right?"
- "Should I continue with [next task] or has priority changed?"

---

## 📝 Before Ending Any Chat

Always do these updates:

### Update PROJECT_STATUS.md
- What we accomplished this session
- What's now working
- What's still not working
- Current blockers
- Timestamp

### Update NEXT_STEPS.md
- Check off completed tasks
- Add any new tasks discovered
- Re-prioritize if needed

### Update DECISION_LOG.md (if applicable)
- Any significant decisions made
- The reasoning behind them

### Update ISSUES_RESOLVED.md (if applicable)
- Any bugs or issues fixed
- Root cause and solution

### Update CHANGELOG.md
- What files were created/modified
- Brief description of changes

---

## 🔴 Important Rules

1. **Never modify AIDN_SPECIFICATION.md** - This is the source of truth
2. **Always update docs before ending a chat** - Future Claude depends on this
3. **Check ISSUES_RESOLVED.md before debugging** - Don't re-solve solved problems
4. **Check DECISION_LOG.md before suggesting alternatives** - We may have already decided against them
5. **Be honest about blockers** - Document them clearly so we can address them

---

## 📊 Project Phases

### PROTOTYPE Phase (Current Goal)
- Get core voice agent working
- Make one successful demo call
- Book one appointment
- Impress YC

### PRODUCT Phase (After YC)
- Full feature set
- Production deployment
- Real customers
- Scale

Always ask: "Is this needed for PROTOTYPE or can it wait for PRODUCT?"