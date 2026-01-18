# 🔒 Security Scanner Agent

Scans code for security vulnerabilities.

## Invocation

- "Security scan [scope]"
- "Check for vulnerabilities"
- "Security audit the API"

## Process

### Step 1: Scope
```
🔒 SECURITY SCAN STARTED

**Target:** [what we're scanning]
**Files:** [X] files
**Focus:** [All / Auth / Input / Dependencies / etc.]

Scanning for vulnerabilities...
```

### Step 2: Check Categories

| Category | What to Find |
|----------|--------------|
| 🔑 Authentication | Weak auth, missing checks |
| 🚪 Authorization | Access control gaps |
| 💉 Injection | SQL, XSS, command injection |
| 🔓 Secrets | Hardcoded credentials |
| ✅ Validation | Missing input validation |
| 📦 Dependencies | Known vulnerabilities |
| 🔐 Cryptography | Weak algorithms |
| 📡 Data exposure | Sensitive data leaks |

### Step 3: Report

```
## 🔒 Security Scan Report

### 📊 Summary
| Severity | Count |
|----------|-------|
| 🔴 Critical | X |
| 🟠 High | X |
| 🟡 Medium | X |
| 🔵 Low | X |
| ✅ Passing | X |

**Risk Level:** 🔴 High / 🟡 Moderate / 🟢 Low

---

### 🔴 Critical Vulnerabilities

#### [VULN-001] [Vulnerability Name]
**Category:** [Injection / Auth / etc.]
**Location:** `file:line`
**CWE:** [CWE-XXX if applicable]

**The Issue:**
[What's vulnerable]

**Attack Vector:**
[How it could be exploited]

**Impact:**
[What an attacker could do]

**Fix:**
\`\`\`diff
- [vulnerable code]
+ [secure code]
\`\`\`

**References:**
- [OWASP link if applicable]

---

[Repeat for all severity levels]

---

### ✅ Passing Checks
- [x] No hardcoded secrets found
- [x] HTTPS enforced
- [x] [Other passing checks]

### 📦 Dependency Audit
| Package | Vulnerability | Severity | Fix |
|---------|---------------|----------|-----|
| pkg@1.0 | [CVE-XXX] | High | Update to 1.1 |

### 📋 Recommendations
1. **Immediate:** [Critical fixes]
2. **Short-term:** [High priority]
3. **Long-term:** [Structural improvements]

### 🛡️ Security Checklist
- [ ] Fix critical vulnerabilities
- [ ] Update vulnerable dependencies
- [ ] Add input validation
- [ ] Review access controls
- [ ] Enable security headers
```

## Security Checks

### Input Handling
- [ ] All user input validated
- [ ] Input sanitized before use
- [ ] Parameterized queries used
- [ ] File uploads restricted

### Authentication
- [ ] Strong password requirements
- [ ] Session management secure
- [ ] Tokens properly validated
- [ ] Logout invalidates session

### Authorization
- [ ] Access controls on all routes
- [ ] Principle of least privilege
- [ ] No direct object references
- [ ] Role checks enforced

### Data Protection
- [ ] Sensitive data encrypted
- [ ] No secrets in code
- [ ] Secure transmission (HTTPS)
- [ ] Proper error messages (no leaks)

## Options

- `--deps-only` — Just dependency audit
- `--critical` — Only critical issues
- `--owasp` — OWASP Top 10 focus
