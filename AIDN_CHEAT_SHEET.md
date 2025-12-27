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

Review the changes made this session and commit them to git with an appropriate commit message, then push to origin.

**Examples of good commit messages:**
- `"Voice agent now connects to Twilio"`
- `"Fixed appointment booking bug"`Rea
- `"Added lead upload feature"`
- `"Updated system prompt for better objections"`

---

## 📁 Important Files to Know

| File | What It Is |
|------|------------|
| `AIDN_SPECIFICATION.md` | The full vision - what we're building |
| `CLAUDE_INSTRUCTIONS.md` | Tells Claude how to onboard itself |
| `docs/PROJECT_STATUS.md` | Current state - what works, what doesn't |
| `docs/NEXT_STEPS.md` | Prioritized todo list |
| `docs/ISSUES_RESOLVED.md` | Bugs already fixed - don't re-solve |
| `docs/DECISION_LOG.md` | Why we made certain choices |

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

---

## 🚀 Daily Workflow

1. Open Cursor
2. Open AIDN project
3. Start new chat → Paste the "Read AIDN_SPECIFICATION.md..." prompt
4. Work on next task
5. When done or taking a break → Save to GitHub
6. Repeat

---

## 📞 Need Help?

Go back to Claude.ai chat and share:
- Screenshot of the error
- What you were trying to do
- What happened instead

I have context on your entire AIDN project!
