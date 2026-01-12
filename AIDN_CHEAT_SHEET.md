# AIDN Quick Reference Cheat Sheet

## 🔄 Starting a New Chat in Cursor

Copy and paste this:
```
Read AIDN_SPECIFICATION.md and /docs, then continue where we left off
```

---

## 💾 Save Your Work to GitHub

Run these commands in terminal after making progress:

```bash
git add .
git commit -m "Describe what you did"
git push
```

### Better Commit Messages (Use Prefixes)

Use prefixes to make history searchable:

```bash
git commit -m "feat: Add Groq LLM support"
git commit -m "fix: Appointment booking bug"
git commit -m "docs: Update README with Telnyx setup"
git commit -m "chore: Remove obsolete files"
```

**Prefix Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `chore:` - Cleanup/maintenance
- `refactor:` - Code restructuring
- `perf:` - Performance improvements

**Examples:**
- `"feat: Voice agent now connects via LiveKit SIP + Telnyx"`
- `"fix: Appointment booking double-booking bug"`
- `"docs: Update architecture with voice optimization status"`
- `"chore: Remove obsolete dashboard files"`

---

## 📁 Important Files to Know

| File | What It Is |
|------|------------|
| `AIDN_SPECIFICATION.md` | The full vision - what we're building |
| `docs/CLAUDE_INSTRUCTIONS.md` | Tells Claude how to onboard itself |
| `docs/PROJECT_STATUS.md` | Current state - what works, what doesn't |
| `docs/NEXT_STEPS.md` | Prioritized todo list |
| `docs/ISSUES_RESOLVED.md` | Bugs already fixed - don't re-solve |
| `docs/DECISION_LOG.md` | Why we made certain choices |
| `docs/YC_DEADLINE_ROADMAP.md` | 5-week plan to Feb 9 deadline |
| `docs/VOICE_OPTIMIZATION_CHECKLIST.md` | Voice latency optimization guide |

---

## 🏷️ Tag Major Milestones

After completing a major feature, tag it so you can always go back:

```bash
# Tag current state
git tag -a v0.2.0 -m "Voice optimization complete"
git push origin v0.2.0

# See all tags
git tag -l

# Go back to a tagged version (if needed)
git checkout v0.2.0
```

**When to tag:**
- After major features complete
- Before YC demo
- After fixing critical bugs
- Version releases

---

## 🆘 If Something Breaks

### Undo last commit (before pushing):
```bash
git reset --soft HEAD~1
```

### See what changed:
```bash
git status
```

### Discard all changes and go back to last save:
```bash
git checkout .
```

### See recent commits:
```bash
git log --oneline -10
```

### Find commits by keyword:
```bash
git log --grep="latency" --oneline
```

---

## 🚀 Daily Workflow

1. Open Cursor
2. Open AIDN project
3. **Pull latest changes:** `git pull origin main`
4. Start new chat → Paste the "Read AIDN_SPECIFICATION.md..." prompt
5. Work on next task
6. **Commit often** (after each logical change):
   ```bash
   git add .
   git commit -m "feat: Description of what you did"
   git push
   ```
7. When done or taking a break → Save to GitHub
8. Repeat

### Before Starting Work
```bash
git pull origin main  # Get latest changes
git status            # See what's changed
```

### After Completing Work
```bash
git add .
git commit -m "feat: What you accomplished"
git push
```

---

## 📞 Need Help?

Go back to Claude.ai chat and share:
- Screenshot of the error
- What you were trying to do
- What happened instead

I have context on your entire AIDN project!
