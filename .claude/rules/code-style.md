# 📝 Code Style Rules

Universal style guidelines. Brainstorm will add project-specific overrides.

## General Principles

### Naming
| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userName`, `isActive` |
| Functions | camelCase | `getUserById`, `handleClick` |
| Classes | PascalCase | `UserService`, `ApiClient` |
| Constants | UPPER_SNAKE | `MAX_RETRIES`, `API_URL` |
| Files | kebab-case or match export | `user-service.ts`, `UserService.ts` |

### Code Organization
```
1. Imports (external → internal → relative)
2. Constants/types
3. Main code
4. Helpers (if small) or separate file
5. Exports
```

### Function Guidelines
- Single responsibility
- Max ~50 lines (extract if longer)
- Max 3-4 parameters (use options object if more)
- Return early for edge cases

### Comments
- **Do:** Explain WHY, not WHAT
- **Do:** Document non-obvious behavior
- **Don't:** Comment obvious code
- **Don't:** Leave commented-out code

## Formatting

### Indentation
- 2 spaces (default, override in project config)

### Line Length
- Max 100 characters (soft limit)
- Max 120 characters (hard limit)

### Braces
```javascript
// Yes
if (condition) {
  doThing();
}

// No
if (condition) { doThing(); }
```

### Whitespace
- Space after keywords: `if (`, `for (`
- Space around operators: `a + b`
- No trailing whitespace
- Single blank line between sections

## Project Overrides

Brainstorm will add project-specific rules here based on:
- Language/framework conventions
- Team preferences
- Linter configuration

---

*Override this file with project-specific rules in `.claude/rules/code-style.md`*
