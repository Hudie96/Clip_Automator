# Pre-Commit Validation Command

Validate changes before committing and generate a commit message.

## Instructions

$ARGUMENTS — Optional commit message. If not provided, Claude will generate one.

### Step 1: Review Staged Changes

```bash
git status
git diff --staged
```

### Step 2: Pre-Commit Checklist

Verify before committing:

#### Code Quality
- [ ] No TODO/FIXME left unaddressed (or intentional)
- [ ] No commented-out code
- [ ] No console.log/print statements for debugging
- [ ] No hardcoded values that should be config

#### Testing
- [ ] All tests pass: `npm test`
- [ ] New code has tests
- [ ] No skipped/disabled tests without reason

#### Standards
- [ ] Linting passes: `npm run lint`
- [ ] Type checking passes: `npm run typecheck`
- [ ] Formatting is correct

#### Security
- [ ] No secrets/credentials in code
- [ ] No sensitive data exposed
- [ ] `.env.example` updated if new env vars

#### Documentation
- [ ] README updated if needed
- [ ] Code comments for complex logic
- [ ] API docs updated if endpoints changed

### Step 3: Generate Commit Message

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation only
- `style` — Formatting, no logic change
- `refactor` — Code change, no new feature or fix
- `test` — Adding or updating tests
- `chore` — Maintenance tasks

**Rules:**
- Subject: imperative mood, no period, <50 chars
- Body: explain what and why, not how
- Footer: reference issues (Closes #123)

### Step 4: Commit

If all checks pass and message is approved:
```bash
git commit -m "[generated message]"
```

### Output Format

```markdown
## 📦 Pre-Commit Report

### Changes Summary
- Files modified: X
- Lines added: +X
- Lines removed: -X

### Validation Results
✅ Tests passing
✅ Linting clean
✅ No secrets detected
⚠️ [any warnings]

### Suggested Commit Message
```
feat(auth): add OAuth login support

- Add Google and GitHub OAuth providers
- Implement token refresh logic
- Add user session management

Closes #42
```

### Commit?
Ready to commit with this message? (y/n)
```

## Example Usage

```
/commit                                    # Auto-generate message
/commit "fix: resolve login timeout"       # Use provided message
/commit --dry-run                          # Validate without committing
```

---

**Good commits tell a story. Make yours count.**
