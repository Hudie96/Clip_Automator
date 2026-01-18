# 🔧 Refactor

Improve this code without changing behavior:

$ARGUMENTS

## Workflow

1. **Understand current behavior**
   - What does this code do?
   - What are its inputs/outputs?
   - What depends on it?

2. **Identify improvement areas**
   - Readability
   - Performance
   - Maintainability
   - Duplication
   - Complexity

3. **Present refactoring plan**
   - What changes
   - What stays the same
   - Risk assessment

4. **Get approval before changing**
   - Show before/after
   - Explain trade-offs

5. **Refactor incrementally**
   - Small steps
   - Verify behavior preserved

## Output Format

### Analysis Phase
```
## 🔧 Refactor: [target]

### 📊 Current State
- Lines: X
- Complexity: [low/medium/high]
- Issues: [list]

### 🎯 Proposed Changes
| Change | Impact | Risk |
|--------|--------|------|
| [change] | [benefit] | 🟢/🟡/🔴 |

### ⚖️ Trade-offs
**Gaining:** [benefits]
**Losing:** [any trade-offs]

Proceed?
```

### After Refactoring
```
## ✅ Refactored: [target]

### 📊 Results
| Metric | Before | After |
|--------|--------|-------|
| Lines | X | Y |
| Complexity | X | Y |

### 🔄 Changes Made
1. [change + why]
2. [change + why]

### ✅ Behavior Preserved
[Confirmation that functionality unchanged]
```

## Refactoring Types

- `/refactor for readability` — Cleaner code
- `/refactor for performance` — Faster execution
- `/refactor extract [thing]` — Pull out reusable piece
- `/refactor simplify` — Reduce complexity
- `/refactor modernize` — Update to newer patterns
