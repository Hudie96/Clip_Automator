# Context Catchup Command

Reload project context after clearing the conversation or starting a new session.

## Instructions

This command helps you resume work by loading:
1. Recent uncommitted changes
2. Current branch and status
3. Recent commit history
4. Any in-progress work

### What to Load

```bash
# Current state
git status
git branch --show-current

# Recent changes
git diff --stat
git diff --name-only

# Recent history
git log --oneline -5

# Check for in-progress work
ls -la SCRATCHPAD.md HANDOFF.md TODO.md 2>/dev/null
```

### Read Key Files

Load context from:
- `HANDOFF.md` — Previous session notes
- `SCRATCHPAD.md` — Work in progress
- `TODO.md` — Outstanding tasks
- Recent PR/issue if applicable

### Output Format

```markdown
## 🔄 Context Loaded

### Current State
- Branch: `feature/user-auth`
- Status: 3 files modified, 1 untracked

### Recent Changes
- `src/auth/login.ts` — (+45, -12)
- `src/auth/types.ts` — (+20, -0)
- `tests/auth.test.ts` — (+30, -5)

### Last 5 Commits
1. `abc123` fix: resolve token refresh issue
2. `def456` feat: add OAuth providers
...

### In-Progress Work
From HANDOFF.md:
> "Working on OAuth flow. Next: implement token refresh callback"

### Ready to Continue
What would you like to work on?
```

## When to Use

- After `/clear` to start fresh but keep context
- Starting a new session on existing work
- Returning to a project after time away
- Onboarding to someone else's WIP

## Arguments

$ARGUMENTS — Optional: specific area to focus on (e.g., "auth", "tests")

## Example Usage

```
/catchup                    # Load all context
/catchup auth               # Focus on auth-related changes
/catchup --full             # Include file contents, not just diffs
```

---

**Fresh context, continued momentum.**
