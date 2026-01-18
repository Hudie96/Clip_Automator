# 🔬 Context

Deep dive into understanding:

$ARGUMENTS

## Workflow

1. **Map the territory**
   - What files are involved?
   - What's the dependency graph?
   - What's the data flow?

2. **Trace through**
   - Entry points
   - Key functions
   - Exit points

3. **Document understanding**
   - Architecture diagram (text-based)
   - Key concepts
   - Gotchas

## Output Format

```
## 🔬 Context: [topic]

### 🗺️ Overview
[High-level explanation]

### 📁 Files Involved
| File | Role |
|------|------|
| `path/file` | [what it does] |

### 🔄 Flow
\`\`\`
[Entry] → [Step 1] → [Step 2] → [Output]
                ↓
           [Side effect]
\`\`\`

### 🔑 Key Concepts
- **[Term]**: [Definition]
- **[Term]**: [Definition]

### 🔗 Dependencies
- Depends on: [what this needs]
- Used by: [what uses this]

### ⚠️ Gotchas
- [Non-obvious things]
- [Common mistakes]

### 📚 Related
- [Related areas to explore]
```

## Usage

- `/context auth flow` — Understand auth system
- `/context data fetching` — How data moves
- `/context [feature]` — Specific feature deep-dive
- `/context this file` — Current file context
