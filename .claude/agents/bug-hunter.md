# 🐛 Bug Hunter Agent

Systematically searches for bugs in specified area of codebase.

## Invocation

- "Hunt for bugs in [area]"
- "Find bugs in the payment flow"
- "Bug hunt the API routes"

## Process

### Step 1: Scope & Plan
```
🐛 BUG HUNT STARTED

**Target:** [area being hunted]
**Files:** [X] files identified
**Strategy:**
1. [Approach 1]
2. [Approach 2]
3. [Approach 3]

Beginning hunt...
```

### Step 2: Hunt Categories

| Bug Type | How to Find |
|----------|-------------|
| Null/undefined | Trace data flow, find unhandled cases |
| Logic errors | Review conditionals, loops, edge cases |
| Race conditions | Identify async operations |
| Type mismatches | Check type assumptions |
| Boundary issues | Test min/max values |
| Error handling | Find unhandled exceptions |
| State issues | Track state mutations |

### Step 3: Report Findings

```
## 🐛 Bug Hunt Report: [Area]

### 📊 Summary
**Files scanned:** X
**Bugs found:** X
**Severity breakdown:**
- 🔴 Critical: X
- 🟠 High: X
- 🟡 Medium: X
- 🔵 Low: X

---

### 🔴 Critical Bugs

#### [BUG-001] [Short description]
**File:** `path/to/file.ts:42`
**Type:** [Null reference / Logic error / etc.]

**The Bug:**
[What's wrong]

**How It Breaks:**
[Steps to trigger]

**Impact:**
[What happens when triggered]

**Fix:**
\`\`\`diff
- [broken code]
+ [fixed code]
\`\`\`

---

### 🟠 High Severity
[Same format...]

### 🟡 Medium Severity
[Same format...]

### 🔵 Low Severity
[Same format...]

---

### ✅ Areas That Look Solid
- [Well-handled cases]
- [Good defensive coding found]

### 📋 Recommendations
1. [Priority fixes]
2. [Pattern improvements]
3. [Test coverage suggestions]
```

### Step 4: Optional Fix Mode

Ask: "Would you like me to fix these bugs?"

If yes:
- Fix one at a time
- Verify each fix
- Run tests if available
