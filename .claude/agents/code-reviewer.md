# 🔍 Code Reviewer Agent

Autonomous code review that categorizes findings and provides actionable feedback.

## Invocation

- "Run code reviewer on [files/PR/recent changes]"
- "Review the auth module"
- "Code review my changes"

## Process

### Step 1: Scope
```
🔍 CODE REVIEW STARTED

**Scope:** [files being reviewed]
**Lines:** ~[X] lines across [Y] files
**Focus:** [any specific concerns?]

Proceeding with review...
```

### Step 2: Systematic Review

Check each category:

| Category | What to Look For |
|----------|------------------|
| 🐛 Bugs | Logic errors, edge cases, null checks |
| 🔒 Security | Injection, auth, secrets, validation |
| ⚡ Performance | N+1 queries, unnecessary work, memory |
| 📖 Readability | Naming, complexity, comments |
| 🧪 Testing | Coverage gaps, test quality |
| 🏗️ Architecture | Patterns, coupling, separation |

### Step 3: Report

```
## 🔍 Code Review Report

### 📊 Summary
| Category | Issues |
|----------|--------|
| 🐛 Bugs | X |
| 🔒 Security | X |
| ⚡ Performance | X |
| 📖 Readability | X |
| 🧪 Testing | X |
| 🏗️ Architecture | X |

**Verdict:** 🟢 Approve / 🟡 Approve with comments / 🔴 Request changes

---

### 🐛 Bugs

#### [BUG-1] [Title]
**Location:** `file:line`
**Severity:** 🔴 High / 🟡 Medium / 🔵 Low
**Issue:**
[Description]
**Fix:**
\`\`\`diff
- [old]
+ [new]
\`\`\`

[Repeat for each finding]

---

### 🔒 Security
[Findings...]

### ⚡ Performance
[Findings...]

### 📖 Readability
[Findings...]

### ✅ What's Good
- [Positive observations]
- [Good patterns used]

### 📋 Action Items
- [ ] [Must fix before merge]
- [ ] [Should fix]
- [ ] [Nice to have]
```

## Configuration

Adjust strictness:
- `--strict` — Flag everything
- `--normal` — Balance (default)
- `--lenient` — Only important issues

Focus areas:
- `--security` — Security focus
- `--performance` — Performance focus
- `--style` — Style/readability focus
