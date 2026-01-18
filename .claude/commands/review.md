# Code Review Command

Perform a comprehensive code review of the specified files or recent changes.

## Instructions

### What to Review
$ARGUMENTS — Specific files, directories, or "recent" for uncommitted changes

If no argument provided, review all uncommitted changes:
```bash
git diff --name-only
```

### Review Checklist

For each file, evaluate:

#### 1. Correctness
- [ ] Logic is sound and handles edge cases
- [ ] Error handling is comprehensive
- [ ] No obvious bugs or race conditions

#### 2. Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation is present
- [ ] No SQL injection or XSS vulnerabilities
- [ ] Sensitive data is properly handled

#### 3. Performance
- [ ] No N+1 queries or unnecessary loops
- [ ] Expensive operations are optimized
- [ ] Memory usage is reasonable

#### 4. Maintainability
- [ ] Code is readable and self-documenting
- [ ] Functions are focused (single responsibility)
- [ ] No code duplication
- [ ] Naming is clear and consistent

#### 5. Testing
- [ ] New code has corresponding tests
- [ ] Tests cover happy path and edge cases
- [ ] No commented-out or skipped tests

#### 6. Standards Compliance
- [ ] Follows project code style
- [ ] Uses established patterns
- [ ] Documentation is updated if needed

### Output Format

```markdown
## 🔍 Code Review: [scope]

### Summary
[1-2 sentence overview]

### ✅ Strengths
- [What's done well]

### ⚠️ Issues Found

#### Critical (Must Fix)
1. **[File:Line]** — [Issue description]
   - Why: [Explanation]
   - Fix: [Suggested solution]

#### Important (Should Fix)
1. **[File:Line]** — [Issue description]

#### Minor (Nice to Have)
1. **[File:Line]** — [Suggestion]

### 📊 Metrics
- Files reviewed: X
- Issues found: X critical, X important, X minor
- Test coverage: [if measurable]

### Verdict
[ ] ✅ Approve
[ ] ⚠️ Approve with comments
[ ] ❌ Request changes
```

## Example Usage

```
/review                           # Review all uncommitted changes
/review src/components/           # Review specific directory
/review src/auth/login.ts         # Review specific file
/review recent                    # Review recent changes
```

---

**Focus on bugs and security issues, not style nitpicks.**
