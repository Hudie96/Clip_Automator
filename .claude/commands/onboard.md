# 🚀 Onboard

Deep dive into a task, feature area, or codebase section before starting work.

$ARGUMENTS

## Purpose

Use this when you need to thoroughly understand something before making changes. This is the "measure twice, cut once" command.

## Workflow

### Phase 1: Scope Definition

```
🎯 ONBOARDING TARGET

**Focus Area:** [what we're exploring]
**Goal:** [what we need to understand]
**Depth:** [surface / moderate / deep]
```

### Phase 2: Discovery

#### 2a. Find Related Files
```bash
# Search for relevant files
find . -type f -name "*.ts" | xargs grep -l "[keyword]" | head -20

# Check recent activity
git log --oneline --all -- "*[pattern]*" | head -10
```

#### 2b. Map Dependencies
```
📊 DEPENDENCY MAP

[target] depends on:
  ├── [dependency 1]
  │   └── [sub-dependency]
  ├── [dependency 2]
  └── [dependency 3]

[target] is used by:
  ├── [consumer 1]
  └── [consumer 2]
```

#### 2c. Understand Data Flow
```
🔄 DATA FLOW

[Entry Point]
    ↓
[Processing Step 1]
    ↓
[Processing Step 2]
    ↓
[Output/Side Effect]
```

### Phase 3: Document Findings

```
## 🧠 Understanding: [Topic]

### What It Does
[High-level explanation]

### Key Files
| File | Purpose |
|------|---------|
| `path/file.ts` | [what it does] |

### Important Functions
| Function | Purpose | Called By |
|----------|---------|-----------|
| `funcName` | [what] | [where] |

### Data Structures
| Type/Interface | Purpose |
|----------------|---------|
| `TypeName` | [what it represents] |

### Patterns Used
- [Pattern 1]: [how it's used here]
- [Pattern 2]: [how it's used here]

### Gotchas
- ⚠️ [Non-obvious thing 1]
- ⚠️ [Non-obvious thing 2]

### Related Documentation
- [Link to relevant docs]
- [Link to related code]
```

### Phase 4: Readiness Check

```
✅ READY TO WORK

**Understanding Level:** [1-5 confidence]

**Can Answer:**
- [ ] What is this code's purpose?
- [ ] How does data flow through it?
- [ ] What depends on this?
- [ ] What are the edge cases?
- [ ] Where are the tests?

**Questions Remaining:**
- [Any open questions]

**Recommended Starting Point:**
[Where to begin making changes]
```

## Options

| Command | What It Does |
|---------|--------------|
| `/onboard [feature]` | Explore a feature area |
| `/onboard [file]` | Deep dive into a file |
| `/onboard [ticket]` | Understand a ticket's scope |
| `/onboard --quick` | Surface-level overview only |
| `/onboard --deep` | Exhaustive exploration |

## Example

```
/onboard the authentication system

/onboard src/api/users.ts

/onboard PROJ-456 --deep
```
