# /agent — Run the Master Agent

Invoke the master agent to coordinate multiple agents for complex tasks.

## Usage

```
/agent [task description]
```

## Examples

```
/agent fix this authentication bug
/agent make src/api/ production-ready
/agent full audit on the payment module
/agent clean up and document utils/
/agent is this code secure?
```

## What Happens

The master agent will:

1. **Analyze** your task
2. **Plan** which agents to run and in what order
3. **Execute** each agent fully
4. **Combine** their outputs
5. **Report** final results with next steps

## Quick Shortcuts

| Say This | Runs These Agents |
|----------|-------------------|
| "quick review" | code-reviewer |
| "find bugs" | bug-hunter |
| "security audit" | security-scanner → code-reviewer |
| "fix and verify" | bug-hunter → test-generator → code-reviewer |
| "full audit" | All 6 agents |
| "production-ready" | bug-hunter → security-scanner → test-generator → doc-writer → code-reviewer |

## Available Agents

| Agent | What It Does |
|-------|--------------|
| 🔍 bug-hunter | Finds bugs and edge cases |
| 🔒 security-scanner | Finds vulnerabilities |
| 🧪 test-generator | Creates tests |
| 📝 doc-writer | Writes documentation |
| 🔧 refactor-bot | Cleans up code |
| ✅ code-reviewer | Reviews code quality |

## Example Output

```
## 🎯 Task: Fix authentication bug

**Plan:**
1. 🔍 bug-hunter — find the issue
2. 🧪 test-generator — add tests
3. ✅ code-reviewer — verify fix

Running...

---
### 🔍 bug-hunter
Found: Null check missing in auth.js:42

---
### 🧪 test-generator  
Created: 3 tests for null cases

---
### ✅ code-reviewer
Approved — fix is correct

---
## ✅ Complete

| Agent | Result |
|-------|--------|
| bug-hunter | Found 1 bug |
| test-generator | Added 3 tests |
| code-reviewer | Approved |

**Next:** /commit to save changes
```

## When to Use

- Complex tasks that need multiple perspectives
- Before merging important code
- Making code production-ready
- Full security/quality audits
- When you're not sure which agent to use

## When NOT to Use

- Simple, single-purpose tasks (just use the specific agent)
- Quick questions (use `/help` instead)
- Just need a code review (use `/review`)
