# How to Check if Files Are Obsolete

## Quick Method: Search for References

### Step 1: Search for the filename in your codebase

```bash
# Search for references to the file
grep -r "filename" . --include="*.py" --include="*.yml" --include="*.md" --include="*.sh"
```

**What to look for:**
- ✅ **If found:** File is likely still in use
- ❌ **If NOT found:** File might be obsolete (but check imports too)

### Step 2: Check for imports

```bash
# Search for imports of the file
grep -r "import.*filename\|from.*filename" . --include="*.py"
```

### Step 3: Check configuration files

```bash
# Check docker-compose files
grep "filename" docker-compose*.yml

# Check README
grep "filename" README.md

# Check any scripts
grep "filename" *.sh
```

### Step 4: Check git history

```bash
# See when file was last modified
git log --all --oneline --follow -- filename.py

# See what changed
git log -p -- filename.py | head -50
```

---

## Example: Checking `simple_dashboard.py`

### ✅ What I Found:

1. **No references found:** 
   - Not imported anywhere
   - Not mentioned in docker-compose.yml
   - Not mentioned in README.md
   - Not mentioned in any scripts

2. **What IS being used:**
   - `src/dashboard_agent/streamlit_app.py` ← **This is the active one**
   - Referenced in `docker-compose.yml` line 66
   - Referenced in `README.md` line 88

3. **Comparison:**
   - `simple_dashboard.py` - Mock data, no database (404 lines)
   - `dashboard_demo.py` - Has database connection (393 lines)
   - `streamlit_app.py` - Full implementation (369 lines) ← **ACTIVE**

### ✅ Conclusion: `simple_dashboard.py` is OBSOLETE

**Why:**
- No references anywhere in codebase
- Replaced by `src/dashboard_agent/streamlit_app.py`
- `dashboard_demo.py` also seems like an older version

---

## Decision Tree

```
Is the file referenced anywhere?
├─ YES → Keep it (it's in use)
└─ NO → Check:
    ├─ Is there a newer version?
    │  ├─ YES → Old file is obsolete
    │  └─ NO → Check git history
    │      ├─ Recently modified? → Might be work in progress
    │      └─ Old and untouched? → Likely obsolete
    └─ Is it a test/example file?
       ├─ YES → Keep if useful for reference
       └─ NO → Consider removing
```

---

## Safe Removal Process

### Before Removing:

1. **Search for references** (as shown above)
2. **Check git history** - see when it was last useful
3. **Compare with similar files** - is there a newer version?
4. **Test your application** - does it still work without it?

### If Safe to Remove:

```bash
# Remove the file
git rm filename.py

# Commit the removal
git commit -m "chore: Remove obsolete filename.py (replaced by new_file.py)"

# Push
git push
```

### If Unsure:

**Option 1: Move to archive folder**
```bash
mkdir -p archive
git mv filename.py archive/
git commit -m "chore: Archive filename.py (may be obsolete)"
```

**Option 2: Add comment in file**
```python
"""
DEPRECATED: This file is no longer used.
Replaced by: src/new_location/new_file.py
Last used: [date]
"""
```

---

## Common Patterns

### Obsolete Files Usually:
- ❌ Have no imports/references
- ❌ Are older versions replaced by newer files
- ❌ Have "old", "simple", "test", "demo" in name
- ❌ Haven't been modified in months
- ❌ Are mentioned in CHANGELOG as removed/replaced

### Active Files Usually:
- ✅ Are imported/used in other files
- ✅ Are referenced in config files (docker-compose, etc.)
- ✅ Are mentioned in README
- ✅ Are in the main source directories (`src/`, `app/`)
- ✅ Have recent git commits

---

## Tools to Help

### 1. Find unused files (Python)
```bash
# Install vulture (unused code detector)
pip install vulture

# Check for unused files
vulture . --min-confidence 80
```

### 2. Find duplicate files
```bash
# Find files with same content
find . -type f -name "*.py" -exec md5sum {} \; | sort | uniq -d -w 32
```

### 3. Git statistics
```bash
# See file age
git log --format="%ai %s" -- filename.py | tail -1

# See when file was last useful
git log --all --oneline -- filename.py | head -5
```

---

## Your Specific Case: `simple_dashboard.py`

**Status:** ✅ **SAFE TO REMOVE**

**Evidence:**
1. No references found in codebase
2. Replaced by `src/dashboard_agent/streamlit_app.py`
3. `dashboard_demo.py` also exists (might be obsolete too)
4. Active dashboard is in `src/dashboard_agent/streamlit_app.py`

**Recommendation:**
- Remove `simple_dashboard.py` ✅
- Check `dashboard_demo.py` too (might also be obsolete)
