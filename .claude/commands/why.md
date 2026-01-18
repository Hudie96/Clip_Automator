# 🤔 Why

Explain the reasoning behind:

$ARGUMENTS

## Workflow

1. **Identify what they're asking about**
   - Code decision?
   - Architecture choice?
   - Pattern used?
   - Historical decision?

2. **Research context**
   - Look at surrounding code
   - Check commit history if relevant
   - Look for comments/docs

3. **Explain the reasoning**
   - What problem was being solved?
   - What alternatives existed?
   - Why was this choice made?

4. **Evaluate current relevance**
   - Is this still the right choice?
   - Has context changed?

## Output Format

```
## 🤔 Why: [thing in question]

### 🎯 The Problem Being Solved
[What need/constraint drove this]

### 🛤️ Alternatives Considered
| Option | Why Not Chosen |
|--------|----------------|
| [alt] | [reason] |

### ✅ Why This Approach
[The reasoning]

### 📅 Still Valid?
[Whether this still makes sense or should be reconsidered]
```

## Examples

- `/why is this using a class instead of a function?`
- `/why are we fetching data this way?`
- `/why is this dependency included?`
- `/why this folder structure?`
