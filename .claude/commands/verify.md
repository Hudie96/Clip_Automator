# Verification & Self-Correction Command

Verify recent changes through automated checks and visual inspection.

## Usage

```
/verify [scope]
```

**Scope options:**
- `last` — Verify last change only
- `session` — Verify all changes this session
- `all` — Full verification suite

## Verification Steps

### Step 1: Identify Changes

```bash
# Get recently modified files
git diff --name-only HEAD~1 2>/dev/null || echo "No git history"

# Or list recently modified
find . -type f -mmin -30 -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null | head -20
```

### Step 2: Run Automated Checks

Execute in order, stop on critical failures:

| Check | Command | Blocks? |
|-------|---------|---------|
| TypeScript | `npx tsc --noEmit` | Yes |
| ESLint | `npx eslint [files]` | Warnings OK |
| Tests | `npm test` | Yes |
| Build | `npm run build` | Yes |

### Step 3: Report Results

```markdown
## ✅ Verification Report

### Files Checked
- `src/components/UserForm.tsx` — Modified
- `src/utils/validation.ts` — Modified
- `src/components/UserForm.test.tsx` — Added

### Automated Checks

| Check | Status | Details |
|-------|--------|---------|
| TypeScript | ✅ Pass | No errors |
| ESLint | ⚠️ 2 warnings | Unused import, missing return type |
| Tests | ✅ Pass | 15/15 passing |
| Build | ✅ Pass | Built in 3.2s |

### Issues Found
1. **Warning:** Unused import in `UserForm.tsx:3`
2. **Warning:** Missing return type in `validation.ts:42`

### Self-Correction Applied
- ✅ Removed unused import
- ✅ Added return type annotation

### Final Status
✅ All checks passing. Ready for commit.
```

## Self-Correction Loop

When issues are found:

```
1. Identify issue type
   ├── Syntax error → Fix immediately
   ├── Type error → Fix immediately
   ├── Lint warning → Fix if simple
   ├── Test failure → Investigate
   └── Build error → Investigate

2. Apply fix

3. Re-run failed check

4. If still failing after 3 attempts:
   └── Report to user, don't loop forever
```

### Automatic Fixes

These can be auto-corrected:
- Unused imports → Remove
- Missing semicolons → Add
- Formatting issues → Run prettier
- Simple type annotations → Infer and add
- Console.log statements → Remove (if in production code)

### Manual Investigation Required

These need human input:
- Logic errors in tests
- Complex type mismatches
- Breaking API changes
- Performance regressions

## Visual Verification (Optional)

If the project has a UI and browser tools are available:

```markdown
### Visual Check

1. Start dev server: `npm run dev`
2. Navigate to affected pages
3. Take screenshots of:
   - [ ] Main view
   - [ ] Edge cases (empty state, error state)
   - [ ] Mobile viewport

**Screenshot comparison:**
| Before | After |
|--------|-------|
| [baseline] | [current] |

Visual diff: No unexpected changes detected.
```

## Integration with Agentic Loop

This command implements the "Verification & Self-Correction" phase:

```
┌─────────────────────┐
│ 1. Gather Context   │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Autonomous Action│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. /verify          │◀── YOU ARE HERE
│    - Run checks     │
│    - Self-correct   │
│    - Report status  │
└──────────┬──────────┘
           ▼
     ┌─────┴─────┐
     │           │
   Pass        Fail
     │           │
     ▼           ▼
  Complete    Loop back
              to step 2
```

## Quick Verification Shortcuts

| Command | What It Does |
|---------|--------------|
| `/verify` | Quick check on recent changes |
| `/verify all` | Full suite (types, lint, test, build) |
| `/check` | Alias for `/verify` |

## Example Output

```
/verify

## ✅ Verification Complete

**Changed files:** 3
**Checks run:** 4
**Issues found:** 1 (auto-fixed)
**Status:** Ready to commit

**Summary:**
- TypeScript: ✅
- ESLint: ✅ (1 warning fixed)
- Tests: ✅ 23 passing
- Build: ✅

No manual intervention needed.
```

---

*Verify early, verify often. Catch issues before they compound.*
