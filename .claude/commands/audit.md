# 🔍 Audit

Security and quality audit of:

$ARGUMENTS

## Workflow

1. **Determine audit scope**
   - Security? Performance? Accessibility?
   - Specific area or full codebase?

2. **Systematic review**
   - Use checklist for audit type
   - Document findings with severity

3. **Prioritize findings**
   - 🔴 Critical — Fix immediately
   - 🟠 High — Fix soon
   - 🟡 Medium — Plan to fix
   - 🔵 Low — Nice to fix

4. **Provide actionable fixes**
   - Each finding gets a remediation

## Output Format

```
## 🔍 Audit Report: [scope]

### 📊 Summary
| Severity | Count |
|----------|-------|
| 🔴 Critical | X |
| 🟠 High | X |
| 🟡 Medium | X |
| 🔵 Low | X |

### 🔴 Critical Issues
**[Issue Name]**
- 📍 Location: [where]
- 🐛 Problem: [what's wrong]
- 💥 Impact: [what could happen]
- ✅ Fix: [how to fix]

### 🟠 High Issues
[Same format]

### 🟡 Medium Issues
[Same format]

### 🔵 Low Issues
[Same format]

### ✅ Passing Checks
- [things that look good]

### 📋 Recommendations
1. [prioritized next steps]
```

## Audit Types

| Type | Focus Areas |
|------|-------------|
| `security` | Auth, injection, secrets, deps |
| `performance` | Speed, memory, queries, bundles |
| `accessibility` | WCAG, keyboard, screen readers |
| `quality` | Patterns, maintainability, tech debt |

## Usage

- `/audit security`
- `/audit performance on /api routes`
- `/audit accessibility`
- `/audit quality on auth module`
