# Git Workflow Standards

## Branch Strategy

### Main Branches
- `main` — Production-ready code
- `develop` — Integration branch (if using gitflow)

### Feature Branches
```
feature/TICKET-123-user-authentication
feature/add-payment-processing
```

### Other Branch Types
```
fix/TICKET-456-login-timeout
hotfix/critical-security-patch
refactor/extract-auth-service
docs/update-api-documentation
```

## Commit Messages

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting, no logic change |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Maintenance |
| `perf` | Performance improvement |

### Rules
- Subject: imperative mood ("add" not "added")
- Subject: no period at end
- Subject: max 50 characters
- Body: explain what and why
- Footer: reference issues

### Examples
```
feat(auth): add OAuth2 login support

Implement Google and GitHub OAuth providers using passport.js.
Token refresh is handled automatically in the background.

Closes #42
```

```
fix(api): handle race condition in user creation

Multiple simultaneous requests could create duplicate users.
Added database-level unique constraint and application retry logic.

Fixes #128
```

## Workflow

### Starting Work
```bash
git checkout main
git pull origin main
git checkout -b feature/TICKET-123-description
```

### During Development
```bash
# Commit early and often
git add -p                    # Stage interactively
git commit -m "feat: ..."     # Commit with message

# Keep branch updated
git fetch origin
git rebase origin/main        # Prefer rebase over merge
```

### Before PR
```bash
# Clean up commits
git rebase -i origin/main     # Squash fixup commits

# Ensure tests pass
npm test
npm run lint

# Push
git push origin feature/TICKET-123-description
```

### Pull Request Checklist
- [ ] Descriptive title
- [ ] Link to ticket/issue
- [ ] Summary of changes
- [ ] Screenshots (if UI)
- [ ] Tests added/updated
- [ ] Self-reviewed the diff

## Code Review

### As Author
- Keep PRs small (<400 lines)
- Respond to feedback constructively
- Explain decisions in PR description

### As Reviewer
- Review within 24 hours
- Be specific and constructive
- Approve when requirements met

## Merge Strategy

Prefer **squash and merge** for:
- Clean history
- Atomic commits
- Easy reverts

Use **rebase and merge** for:
- Preserving commit history
- Multiple logical commits

## Emergency Hotfix

```bash
git checkout main
git checkout -b hotfix/critical-issue
# Make fix
git commit -m "hotfix: fix critical issue"
git push origin hotfix/critical-issue
# Fast-track PR review
# Merge to main
# Deploy immediately
# Backport to develop if needed
```

---

*Good Git hygiene makes collaboration seamless.*
