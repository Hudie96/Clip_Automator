# 🔧 Refactor Bot Agent

Identifies and applies refactoring opportunities.

## Invocation

- "Refactor [target]"
- "Clean up the utils folder"
- "Refactor for readability"

## Process

### Step 1: Analyze
```
🔧 REFACTOR ANALYSIS STARTED

**Target:** [what we're refactoring]
**Scope:** [X] files, ~[Y] lines
**Focus:** [Readability / Performance / Structure / All]

Scanning for opportunities...
```

### Step 2: Identify Opportunities

| Smell | Refactoring |
|-------|-------------|
| Long function | Extract functions |
| Duplicate code | Extract shared utility |
| Deep nesting | Early returns, guard clauses |
| Magic numbers | Named constants |
| God class | Split responsibilities |
| Long parameter list | Options object |
| Complex conditional | Strategy pattern / polymorphism |
| Dead code | Remove it |

### Step 3: Present Plan

```
## 🔧 Refactoring Plan

### 📊 Overview
| Category | Opportunities |
|----------|---------------|
| Extract function | X |
| Remove duplication | X |
| Simplify logic | X |
| Rename for clarity | X |
| Remove dead code | X |

### 📋 Proposed Changes

#### 1. [Refactoring Title]
**File:** `path/to/file.ts`
**Type:** [Extract / Simplify / Rename / etc.]
**Risk:** 🟢 Low / 🟡 Medium / 🔴 High

**Current:**
\`\`\`javascript
[current code]
\`\`\`

**Proposed:**
\`\`\`javascript
[refactored code]
\`\`\`

**Why:** [Benefit of this change]

---

[Repeat for each refactoring]

### ⚖️ Trade-offs
**Gaining:**
- ✅ [improvement]

**Giving up:**
- ❌ [any trade-off]

### 📋 Execution Order
1. [Safest changes first]
2. [Then dependent changes]
3. [Riskier changes last]

Proceed with refactoring?
```

### Step 4: Execute

If approved:
- Apply one refactoring at a time
- Verify behavior preserved
- Commit checkpoint if requested
- Report progress

```
🔧 REFACTORING PROGRESS

✅ [Refactoring 1] — Complete
✅ [Refactoring 2] — Complete
⏳ [Refactoring 3] — In progress
⬜ [Refactoring 4] — Pending
```

### Step 5: Summary

```
🔧 REFACTORING COMPLETE

### 📊 Results
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Lines | X | Y | -Z% |
| Functions | X | Y | +Z |
| Avg length | X | Y | -Z% |
| Complexity | X | Y | -Z% |

### ✅ Changes Applied
1. [Change + benefit]
2. [Change + benefit]

### 🧪 Verify
\`\`\`bash
npm test
\`\`\`

### ⚠️ Manual Checks Needed
- [Anything that needs human verification]
```

## Options

- `--safe` — Only low-risk refactors
- `--aggressive` — Include structural changes
- `--dry-run` — Show plan without applying
