# AIDN v2 Integration Guide
## From 3-4 Second Latency to <1 Second

---

## What Changed

| Component | Before (v1) | After (v2) |
|-----------|-------------|------------|
| System Prompt | 190 lines, ~5000 tokens | 66 lines, ~580 tokens |
| Objection Handling | Baked into prompt | RAG tool lookup |
| Expected Latency | 3-4 seconds | <1 second |

---

## Files Created

```
aidn_refactor/
├── core_prompt.py      # Slim system prompt builder
├── objection_kb.json   # All objection handlers (RAG source)
└── aidn_agent_v2.py    # New agent with RAG tool
```

---

## How to Integrate

### Step 1: Copy Files to Your Project

Copy these files to your `src/voice_agent/` directory:

```bash
# In your AIDN project
cp core_prompt.py src/voice_agent/
cp objection_kb.json src/voice_agent/
cp aidn_agent_v2.py src/voice_agent/
```

### Step 2: Fix Imports in aidn_agent_v2.py

The imports are commented out - you'll need to adjust them for your project structure:

```python
# Change these lines in aidn_agent_v2.py

# FROM:
# from ..shared.database import DatabaseManager, LeadRepository, AppointmentRepository
# from ..shared.models import Lead

# TO (adjust to your actual paths):
from ..shared.database import DatabaseManager, LeadRepository, AppointmentRepository
from ..shared.models import Lead
```

### Step 3: Update main.py to Use v2 Agent

In your `main.py`, change the import:

```python
# FROM:
from .aidn_agent import AIDNVoiceAgent

# TO:
from .aidn_agent_v2 import AIDNVoiceAgentV2 as AIDNVoiceAgent
```

That's it! The agent has the same interface, so no other changes needed.

---

## How the RAG Tool Works

When Aiden hears an objection:

```
User: "I'm not interested"
       ↓
Aiden sees it's an objection
       ↓
Calls: get_objection_response("I'm not interested")
       ↓
RAG looks up in objection_kb.json → finds "not_interested_1"
       ↓
Returns formatted response with lead info filled in
       ↓
Aiden speaks the response
```

The key is that the 16 objection scripts are NOT in the system prompt anymore - they're only loaded when needed.

---

## Testing

### Test 1: Verify Token Reduction

```bash
cd src/voice_agent
python3 -c "
from core_prompt import build_core_prompt
prompt = build_core_prompt()
print(f'Prompt length: {len(prompt)} chars')
print(f'Estimated tokens: {len(prompt) // 4}')
"
```

Expected: ~580 tokens (down from ~5000)

### Test 2: Test RAG Lookup

```bash
python3 -c "
import json
with open('objection_kb.json') as f:
    data = json.load(f)
print(f'Loaded {len(data[\"objections\"])} objection handlers')
"
```

Expected: 16 objection handlers

### Test 3: Make a Test Call

Call your test number and try these objections:
- "What is it?"
- "I'm not interested"
- "How did you get my number?"

Watch the logs for:
```
RAG objection lookup: 'what is it' → what_is_it_1
⏱️ RESPONSE_LATENCY: 450ms
```

---

## Customizing Objections

Edit `objection_kb.json` to:

1. **Add new objections**: Add a new object to the `objections` array
2. **Add trigger phrases**: Add to the `triggers` array
3. **Modify responses**: Edit the `response` field

Example - adding a new objection:

```json
{
  "id": "too_expensive",
  "name": "Too expensive / Can't afford",
  "triggers": ["too expensive", "can't afford", "don't have money"],
  "strategy": "Explain it's free info, no obligation",
  "response": "Oh no no, this is just information - there's no cost to have {agent_name} stop by. They're just gonna go over what's available for your age group. Morning or afternoon work better?"
}
```

---

## Expected Results

After integration:

| Metric | Before | After |
|--------|--------|-------|
| Response latency | 3-4 seconds | <1 second |
| Tokens per turn | ~5000+ | ~800-1000 |
| Prompt size | 190 lines | 66 lines |
| Objection flexibility | Edit huge prompt | Edit JSON file |

---

## Troubleshooting

### "RAG not finding objections"
- Check trigger phrases in `objection_kb.json`
- Add more trigger variations
- Consider adding fuzzy matching later

### "Still slow"
- Check logs for `RESPONSE_LATENCY`
- Ensure using `gpt-4o-mini` not `gpt-4`
- Verify Cartesia TTS is active

### "Objection responses sound wrong"
- Edit `objection_kb.json` directly
- Test by calling `get_objection_response` manually

---

## Next Steps

1. **Integrate and test** - Get v2 running with a test call
2. **Measure latency** - Compare before/after response times
3. **Tune triggers** - Add more trigger phrases as needed
4. **Consider semantic search** - For better objection matching (future)

---

## Questions for Claude Code

Give Claude Code this prompt to integrate:

```
I have 3 new files for AIDN that implement the 3-layer architecture we discussed:
- core_prompt.py (slim 66-line system prompt)
- objection_kb.json (RAG knowledge base for objections)
- aidn_agent_v2.py (new agent with RAG tool)

Please:
1. Copy these into src/voice_agent/
2. Fix the imports in aidn_agent_v2.py for my project structure
3. Update main.py to use AIDNVoiceAgentV2
4. Run a test to verify the prompt is now ~580 tokens instead of ~5000
```
