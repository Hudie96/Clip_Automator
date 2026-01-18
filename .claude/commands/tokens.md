# /tokens — Check Token Usage & Save Money

Analyze current context size and suggest ways to reduce token usage.

## What To Do

### Step 1: Estimate Current Context

Check what's loaded and estimate tokens:

```bash
# Count lines in key files
wc -l CLAUDE.md .claude/**/*.md 2>/dev/null | tail -1

# Check if .claudeignore exists
ls -la .claudeignore 2>/dev/null

# Check for large folders that might be read
du -sh node_modules/ dist/ build/ .git/ venv/ target/ 2>/dev/null
```

### Step 2: Report Current State

Present findings:

```
## 📊 Token Usage Report

### Current Context
| Item | Est. Tokens | Notes |
|------|-------------|-------|
| CLAUDE.md | ~X | Project memory |
| Commands (27) | ~X | Slash commands |
| Rules (7) | ~X | Coding standards |
| Skills (5) | ~X | AI skills |
| **Total Config** | **~X** | |

### .claudeignore Status
✅ Active — ignoring [X] patterns
OR
⚠️ Missing — create one to save tokens!

### Large Folders Detected
| Folder | Size | Status |
|--------|------|--------|
| node_modules/ | 500MB | ✅ Ignored |
| .git/ | 50MB | ✅ Ignored |
| dist/ | 10MB | ⚠️ Not ignored |
```

### Step 3: Suggest Improvements

Based on findings:

**If .claudeignore is missing:**
> "You don't have a `.claudeignore` file. This means Claude might read unnecessary files.
>
> Want me to create one for your stack? This could save significant tokens."

**If large folders aren't ignored:**
> "I found some large folders that aren't in `.claudeignore`:
> - `dist/` (10MB) — generated files
> - `coverage/` (5MB) — test reports
>
> Add these to save tokens?"

**If everything looks good:**
> "Your setup is optimized. `.claudeignore` is covering the big folders."

### Step 4: Offer Quick Fixes

```
## 🔧 Quick Fixes Available

1. **Create .claudeignore** — Save ~50% tokens
2. **Add [folder] to ignore** — Save ~X tokens
3. **Trim CLAUDE.md** — Remove unused sections

Which would you like to do?
```

## Token Estimation Rules

Rough estimates for planning:
- 1 token ≈ 4 characters (English)
- 1 token ≈ 0.75 words
- Typical markdown file: ~100-500 tokens
- node_modules/: 1M+ tokens if read (why we ignore it)
- .git/: 100K+ tokens if read

## Example Output

```
## 📊 Token Usage Report

### Current Context
| Item | Est. Tokens |
|------|-------------|
| CLAUDE.md | ~800 |
| Commands | ~4,000 |
| Rules | ~2,000 |
| Skills | ~3,000 |
| **Total** | **~10,000** |

### .claudeignore
✅ Active — 15 patterns
- node_modules/ ✅
- dist/ ✅
- .git/ ✅
- *.lock ✅

### Suggestions
None — you're optimized! 🎉
```

## Model Cost Optimization

When analyzing token usage, also consider model selection:

### Cost by Model (Approximate)

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| **Opus 4.5** | $15/M | $75/M | Complex planning, security |
| **Sonnet 4.5** | $3/M | $15/M | Standard coding tasks |
| **Haiku** | $0.25/M | $1.25/M | Quick checks, validation |

### Savings Example

```
Task: Review and fix 10 files

All Opus:     ~$5.00
Smart routing: ~$1.50 (70% savings)

Breakdown:
- Haiku: Categorize files, quick checks
- Sonnet: Standard reviews/fixes
- Opus: Security-critical files only
```

### Recommendations

When `/tokens` shows high usage:

1. **Use Haiku for pre-filtering**
   - File categorization
   - Simple searches
   - Validation checks

2. **Use Sonnet for main work**
   - Most coding tasks
   - Standard reviews
   - Test generation

3. **Reserve Opus for**
   - Security audits
   - Complex architecture
   - Production-critical code

## When to Use This

- Before a long coding session
- If responses seem slow
- If you're hitting context limits
- After adding new dependencies
- Monthly checkup
- When costs seem higher than expected
