# 📝 Summarize

Create a concise summary of:

$ARGUMENTS

## Workflow

1. **Identify scope**
   - File? Module? Conversation? Codebase area?

2. **Extract key points**
   - Main purpose
   - Important details
   - Decisions made

3. **Compress to essentials**
   - Remove fluff
   - Keep actionable info

## Output Format

```
## 📝 Summary: [scope]

### 🎯 TL;DR
[One sentence summary]

### 📋 Key Points
- [Important point 1]
- [Important point 2]
- [Important point 3]

### 💡 Decisions/Conclusions
| Decision | Rationale |
|----------|-----------|
| [what] | [why] |

### ⏭️ Next Steps
- [ ] [Action item]
```

## Scope Options

| Target | What It Summarizes |
|--------|-------------------|
| `this file` | Current file's purpose |
| `this conversation` | Chat so far |
| `recent changes` | Recent commits/modifications |
| `[feature]` | Specific feature area |
| `[meeting notes]` | Pasted content |

## Usage

- `/summarize this file`
- `/summarize our conversation`
- `/summarize recent changes`
- `/summarize the auth module`
- `/summarize` + paste content
