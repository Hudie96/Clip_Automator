# 🔧 Fix

Fix this specific error:

$ARGUMENTS

## Workflow

1. **Parse the error**
   - What type of error?
   - Where does it point?
   - What's the stack trace?

2. **Locate the problem**
   - Go to the source
   - Understand the context

3. **Diagnose root cause**
   - Not just symptoms
   - Why is this happening?

4. **Apply fix**
   - Minimal change needed
   - Don't over-engineer

5. **Verify**
   - Error should be gone
   - No new issues introduced

## Output Format

```
## 🔧 Fix: [error type]

### 🐛 Error
\`\`\`
[The error message]
\`\`\`

### 📍 Location
`[file:line]`

### 💡 Cause
[Why this is happening]

### ✅ Fix
\`\`\`diff
- [old code]
+ [new code]
\`\`\`

### 🔍 Explanation
[Why this fixes it]

### 🛡️ Prevention
[How to avoid this in the future]
```

## Common Error Patterns

| Error Type | Usual Cause |
|------------|-------------|
| `undefined is not...` | Missing null check |
| `Cannot read property` | Object doesn't exist |
| `Module not found` | Import path wrong |
| `Type error` | Wrong data type |
| `Syntax error` | Typo or missing bracket |

## Usage

- `/fix` + paste error
- `/fix TypeError: Cannot read property 'x' of undefined`
- `/fix the failing test`
