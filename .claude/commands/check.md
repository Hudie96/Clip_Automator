# ✅ Check

Quick review of recent code or specified target.

$ARGUMENTS

## Workflow

1. **Identify scope**
   - If no target specified, check recently modified files
   - If target specified, focus there

2. **Scan for issues**
   - 🔴 Bugs (will break)
   - 🟡 Warnings (might cause issues)
   - 🔵 Suggestions (improvements)

3. **Report concisely**
   - Group by severity
   - Show location + fix
   - Skip nitpicks unless asked

## Output Format

```
## ✅ Check Results

### 🔴 Bugs (X found)
**[file:line]** - [issue]
└─ Fix: [solution]

### 🟡 Warnings (X found)
**[file:line]** - [issue]
└─ Fix: [solution]

### 🔵 Suggestions (X found)
**[file:line]** - [improvement]
└─ Consider: [solution]

### ✅ Looks Good
- [positive observations]
```

## Scope Options

- `/check` — Recent changes
- `/check [file]` — Specific file
- `/check [function]` — Specific function
- `/check --deep` — More thorough review (use `/review` for this)
