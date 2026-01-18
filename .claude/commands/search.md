# 🔎 Search

Search the codebase for:

$ARGUMENTS

## Workflow

1. **Understand intent**
   - Looking for usage?
   - Looking for definition?
   - Looking for pattern?

2. **Search strategically**
   - File names
   - Function/class names
   - String literals
   - Patterns

3. **Present findings**
   - Grouped by relevance
   - With context

## Output Format

```
## 🔎 Search: "[query]"

### 📍 Found X matches

#### Definitions
| Location | Type |
|----------|------|
| `file:line` | function/class/etc |

#### Usages
| Location | Context |
|----------|---------|
| `file:line` | [how it's used] |

#### Related
- [Other relevant findings]
```

## Search Types

| Query Format | Searches For |
|--------------|--------------|
| `functionName` | Function definitions & calls |
| `"literal string"` | Exact string matches |
| `ClassName` | Class definitions & usages |
| `*.extension` | Files by type |
| `/pattern/` | Regex pattern |

## Usage

- `/search handleSubmit` — Find function
- `/search "TODO"` — Find all TODOs
- `/search where is auth used` — Semantic search
- `/search files that import lodash` — Dependency search
