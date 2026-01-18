# 🤖 GitHub Actions Documentation

Automate Claude Code in your CI/CD pipeline.

## Available Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| PR Review | PR open, `@claude` mention | Automated code review |
| Docs Sync | Monthly schedule | Keep docs aligned with code |
| Code Quality | Weekly schedule | Find and fix quality issues |
| Dependency Audit | Biweekly schedule | Update dependencies safely |

## Setup

### 1. Add API Key Secret

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your API key from console.anthropic.com

### 2. Install Claude GitHub App (Optional but Recommended)

For better PR integration:
1. Visit https://github.com/apps/claude
2. Install on your repository
3. This allows Claude to post as "Claude" instead of "github-actions[bot]"

### 3. Enable Workflows

Workflows are in `.github/workflows/`. They're enabled by default when you push them.

## Workflows in Detail

### PR Review (`pr-claude-review.yml`)

**Triggers:**
- Pull request opened
- Pull request updated (synchronize)
- Comment containing `@claude`

**What it does:**
1. Checks out code with full history
2. Runs Claude to analyze the diff
3. Posts review comment on PR

**Customizing the review:**

Edit the `prompt` section in the workflow:

```yaml
prompt: |
  Review this PR focusing on:
  - Security vulnerabilities
  - Performance issues
  - Test coverage
  
  Use our coding standards in CLAUDE.md
```

**Usage:**
- Automatic on PR open
- Comment `@claude review this` for on-demand review
- Comment `@claude fix the linting errors` for implementation

---

### Docs Sync (`scheduled-docs-sync.yml`)

**Triggers:**
- Scheduled: 1st of each month at 9:00 AM UTC
- Manual: workflow_dispatch

**What it does:**
1. Analyzes commits from the last month
2. Compares code changes to documentation
3. Updates outdated docs
4. Creates a PR with changes

**Customizing:**

Adjust the schedule:
```yaml
on:
  schedule:
    - cron: '0 9 1 * *'  # Monthly
    # - cron: '0 9 * * 1'  # Weekly (Mondays)
```

---

### Code Quality (`scheduled-code-quality.yml`)

**Triggers:**
- Scheduled: Sundays at 2:00 AM UTC
- Manual: workflow_dispatch with optional target directory

**What it does:**
1. Selects a random source directory (or specified one)
2. Runs linters and type checkers
3. Identifies code smells
4. Auto-fixes what it can
5. Creates issues for manual fixes
6. Creates PR with fixes

**Manual trigger:**
1. Go to Actions → "Scheduled - Code Quality"
2. Click "Run workflow"
3. Optionally specify target directory

---

### Dependency Audit (`scheduled-dependency-audit.yml`)

**Triggers:**
- Scheduled: 1st and 15th of each month at 3:00 AM UTC
- Manual: workflow_dispatch with update type selection

**What it does:**
1. Runs `npm audit` or `pip-audit`
2. Checks for outdated packages
3. Applies safe updates based on type:
   - `patch`: x.x.PATCH only (safest)
   - `minor`: x.MINOR.x (usually safe)
   - `major`: MAJOR.x.x (review needed)
   - `security-only`: Only security fixes
4. Runs tests after updates
5. Creates PR with successful updates

**Update types:**

| Type | Updates | Risk |
|------|---------|------|
| `patch` | 1.0.0 → 1.0.1 | 🟢 Very Low |
| `minor` | 1.0.0 → 1.1.0 | 🟡 Low |
| `major` | 1.0.0 → 2.0.0 | 🔴 Medium |
| `security-only` | Only CVE fixes | 🟢 Very Low |

## Cost Estimates

Claude API usage costs vary by model and prompt length.

| Workflow | Frequency | Est. Cost |
|----------|-----------|-----------|
| PR Review | Per PR (~5/week) | $0.25 - $2.50/week |
| Docs Sync | Monthly | $0.50 - $2.00/month |
| Code Quality | Weekly | $1.00 - $5.00/week |
| Dependency Audit | Biweekly | $0.40 - $2.00/month |

**Estimated monthly total:** $10 - $50 (depending on activity)

## Customization

### Using Different Models

Change the model in workflow:
```yaml
with:
  model: "claude-sonnet-4-20250514"    # Faster, cheaper
  # model: "claude-opus-4-20250514"    # More capable
```

### Adding Custom Workflows

Create a new file in `.github/workflows/`:

```yaml
name: My Custom Workflow

on:
  push:
    branches: [main]

jobs:
  custom-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Your instructions here...
```

### Limiting Scope

To save costs, limit what Claude analyzes:

```yaml
prompt: |
  Only review files in src/api/
  Ignore test files and documentation
```

## Troubleshooting

### Workflow Not Running

1. Check workflow is enabled (Actions tab)
2. Verify trigger conditions are met
3. Check for syntax errors in YAML

### Claude Errors

1. Verify `ANTHROPIC_API_KEY` secret is set
2. Check API key has sufficient credits
3. Look at workflow logs for error details

### PR Comments Not Posting

1. Verify workflow has `pull-requests: write` permission
2. Check GitHub App is installed (if using)
3. Ensure PR is from same repository (not fork)

### Rate Limits

If hitting API limits:
1. Reduce workflow frequency
2. Add concurrency limits:
   ```yaml
   concurrency:
     group: claude-${{ github.ref }}
     cancel-in-progress: true
   ```

## Security Considerations

1. **API Key Protection**
   - Only stored as GitHub secret
   - Never logged or exposed
   - Rotated periodically

2. **Permissions**
   - Workflows use minimal required permissions
   - Fork PRs may have limited access

3. **Code Changes**
   - All Claude changes go through PR
   - Human review still required for merge
