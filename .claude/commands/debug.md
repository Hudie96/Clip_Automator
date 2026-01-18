# Systematic Debugging Command

Debug an issue using a structured, methodical approach.

## Instructions

$ARGUMENTS — Error message, symptom description, or file with the bug

### Step 1: Reproduce the Issue

Before fixing, confirm you can reproduce:
- What's the exact error message?
- What steps trigger the bug?
- Is it consistent or intermittent?

### Step 2: Gather Context

Collect information:
```bash
# Check recent changes
git log --oneline -10
git diff HEAD~3

# Check logs
tail -100 logs/error.log

# Check environment
node --version
npm list --depth=0
```

### Step 3: Form Hypotheses

Based on the error, list possible causes:
1. Most likely: [hypothesis]
2. Possible: [hypothesis]
3. Unlikely but check: [hypothesis]

### Step 4: Investigate Systematically

For each hypothesis:
1. Add strategic logging/debugging
2. Test the theory
3. Confirm or eliminate

Use these debugging techniques:
- **Binary search**: Comment out half the code to isolate
- **Print debugging**: Add console.log at key points
- **Rubber duck**: Explain the code line by line
- **Check assumptions**: Verify inputs, types, state

### Step 5: Identify Root Cause

Before fixing, answer:
- What exactly is wrong?
- Why did it happen?
- When was it introduced?

### Step 6: Fix and Verify

1. Make the minimal fix
2. Run the failing test/reproduction steps
3. Verify the fix works
4. Check for regressions
5. Clean up debug code

### Step 7: Prevent Recurrence

- Add a test that would have caught this
- Update documentation if unclear
- Consider if this indicates a broader issue

### Output Format

```markdown
## 🐛 Debug Report: [issue summary]

### Symptom
[What the user experienced]

### Root Cause
[What was actually wrong]

### Investigation Path
1. Hypothesis: [X] → Result: [eliminated/confirmed]
2. Hypothesis: [Y] → Result: [eliminated/confirmed]
3. Found: [root cause]

### Fix Applied
- File: [path]
- Change: [description]

### Verification
- [ ] Original issue no longer occurs
- [ ] Added test to prevent regression
- [ ] No new issues introduced

### Prevention
[How to prevent similar bugs]
```

## Common Debugging Patterns

### "It was working yesterday"
```bash
git bisect start
git bisect bad HEAD
git bisect good <last-known-good-commit>
```

### "Works on my machine"
- Check environment differences
- Compare node_modules
- Check env variables

### "Random failures"
- Look for race conditions
- Check async/await usage
- Look for shared mutable state

### "Silent failures"
- Add error boundaries
- Check Promise rejections
- Look for swallowed errors

## Example Usage

```
/debug TypeError: Cannot read property 'id' of undefined
/debug "Login button doesn't respond"
/debug src/api/users.ts
/debug --bisect feature broke after last deploy
```

---

**Debugging is detective work. Follow the evidence.**
