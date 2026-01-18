# 📖 Quick Reference Guide

Everything you can use in Claude Code, organized by category.

---

## ⚡ Commands (Slash Commands)

Type these in Claude Code to trigger specific workflows.

### 🆘 Getting Help

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/help [problem]` | Debug issues with guided questions | When something's broken |
| `/explain [code]` | Explains code in plain language | When you don't understand something |
| `/stuck` | Analyzes where you are and suggests next steps | When you're lost |
| `/why [code/decision]` | Explains the reasoning behind code or architecture | When you want to understand intent |
| `/tokens` | Check token usage and suggest savings | When you want to optimize costs |

### 🏗️ Building & Planning

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/plan [feature]` | Creates implementation plan before coding | Before starting any new feature |
| `/build [thing]` | Builds something step-by-step with explanations | When you want to create something |
| `/scaffold [type]` | Generates boilerplate structure | Starting new components/modules |
| `/refactor [target]` | Improves code without changing behavior | When code works but is messy |

### ✅ Quality & Review

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/check` | Quick review for bugs and issues | Quick sanity check |
| `/review [scope]` | Deep code review with specific feedback | Before merging/committing |
| `/test [target]` | Generates tests for code | After building features |
| `/audit [area]` | Security/performance audit | Before releases |

### 📝 Git & Documentation

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/commit` | Validates changes and writes commit message | Before committing |
| `/pr [base]` | Generates PR description | Before opening PR |
| `/doc [target]` | Generates documentation | When code needs docs |
| `/changelog [range]` | Summarizes changes for a release | Before releases |

### 🔄 Context & Handoff

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/catchup` | Summarizes recent changes in codebase | Starting a session |
| `/handoff` | Creates summary for another dev/AI | Ending a session |
| `/context [topic]` | Deep-dives into specific area | When you need to understand a system |
| `/summarize [scope]` | Creates concise summary | When you need overview |

### 🛠️ Utilities

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `/fix [error]` | Fixes a specific error | When you have an error message |
| `/search [query]` | Searches codebase semantically | Finding relevant code |
| `/deps` | Analyzes dependencies | Checking for issues/updates |
| `/env` | Helps with environment setup | Setting up dev environment |

---

## 🧠 Skills

Skills are specialized knowledge areas Claude can tap into. They activate automatically when relevant, or you can invoke them directly.

### Universal Skills

| Skill | What It Does | Auto-Activates When |
|-------|--------------|---------------------|
| `brainstorm` | Sets up/customizes your `.claude` config | Setting up new project |
| `research` | Deep research on topics with sources | You need thorough investigation |
| `debug-detective` | Systematic debugging methodology | Tricky bugs that need investigation |
| `code-teacher` | Explains concepts with examples | Learning new things |
| `decision-helper` | Presents options with pro/con tables | Facing architectural choices |

### Domain Skills (Added by Brainstorm)

These get added based on your project type:

| Skill | Added For | What It Does |
|-------|-----------|--------------|
| `api-design` | Backend projects | REST/GraphQL patterns |
| `react-patterns` | React projects | Component patterns, hooks |
| `database-design` | DB projects | Schema design, queries |
| `auth-patterns` | Auth-heavy apps | Security patterns |
| `testing-strategy` | All projects | Test architecture |

---

## 🤖 Agents

Agents are autonomous workflows that can run multi-step tasks.

### Universal Agents

| Agent | What It Does | How to Invoke |
|-------|--------------|---------------|
| `code-reviewer` | Autonomous code review with categories | "Run code reviewer on [files]" |
| `bug-hunter` | Systematically finds bugs | "Hunt for bugs in [area]" |
| `doc-writer` | Generates comprehensive docs | "Document [target]" |
| `test-generator` | Creates test suites | "Generate tests for [target]" |
| `refactor-bot` | Suggests and applies refactors | "Refactor [target]" |
| `security-scanner` | Checks for security issues | "Security scan [scope]" |

### How Agents Differ from Commands

| Aspect | Commands | Agents |
|--------|----------|--------|
| **Scope** | Single task | Multi-step workflow |
| **Interaction** | Usually one response | May ask questions mid-way |
| **Autonomy** | You direct each step | Agent decides next steps |
| **Output** | Direct answer | Report + actions |

---

## 🗂️ Rules

Rules are guidelines Claude follows automatically. You don't invoke them — they're always active.

### Universal Rules

| Rule File | What It Governs |
|-----------|-----------------|
| `code-style.md` | Formatting, naming conventions |
| `error-handling.md` | How to handle errors |
| `git-workflow.md` | Commits, branches, PRs |
| `communication.md` | How Claude talks to you |

### Project-Specific Rules (Added by Brainstorm)

| Rule File | Added For |
|-----------|-----------|
| `api-design.md` | API projects |
| `database.md` | DB projects |
| `testing.md` | All projects |
| `[framework].md` | Based on your stack |

---

## 🔧 How Brainstorm Customizes These

When you run the brainstorm skill on a new project:

### What It Does to Commands

| Before | After |
|--------|-------|
| Generic `/build` | Customized with your stack's patterns |
| Generic `/test` | Uses your testing framework |
| Generic `/commit` | Follows your team's conventions |

### What It Adds

Based on your project type:
- 📁 Project-specific commands
- 🧠 Domain skills
- 📋 Relevant rules
- 🤖 Configured agents

### What It Doesn't Touch

These stay universal:
- `/help`, `/explain`, `/stuck` (always useful)
- `/catchup`, `/handoff` (always needed)
- Core agents (work on any codebase)

---

## 💡 Tips

### Command Chaining

You can use commands in sequence:
```
/plan add user authentication
[review plan]
/build the plan above
/test the new auth module
/commit
```

### When to Use What

| Situation | Use |
|-----------|-----|
| Quick question | Just ask Claude |
| Specific workflow | `/command` |
| Need expertise | Skill (auto or invoke) |
| Multi-step task | Agent |
| Ongoing guidance | Rules (automatic) |

### Customizing Commands

Edit files in `.claude/commands/` to:
- Change the workflow
- Add project-specific steps
- Adjust the output format

---

## 📊 At a Glance

| Category | Count | Location |
|----------|-------|----------|
| Commands | 30 | `.claude/commands/` |
| Skills | 5 | `.claude/skills/` |
| Agents | 7 | `.claude/agents/` |
| Rules | 7 | `.claude/rules/` |
| Hooks | 4 events | `.claude/settings.json` |
| GitHub Actions | 4 workflows | `.github/workflows/` |

---

## 🪝 Hooks

Hooks run automatically before/after Claude takes actions.

| Event | When | Use Case |
|-------|------|----------|
| `PreToolUse` | Before tool runs | Block edits on main branch |
| `PostToolUse` | After tool completes | Auto-format code |
| `SessionStart` | Session begins | Show project info |
| `Stop` | Agent finishes | Notifications |

### Active Hooks in This Template

| Hook | What It Does |
|------|--------------|
| Branch protection | 🚫 Blocks edits on main/master |
| Dangerous command blocker | 🚫 Blocks `rm -rf /`, `sudo`, etc. |
| Auto-format | ✨ Runs Prettier/Black after edits |
| Test notification | 🧪 Reminds you to run tests |
| Session info | 📂 Shows project & branch on start |

📚 **Docs:** `.claude/docs/HOOKS.md`

---

## 🔌 MCP Servers

Connect Claude to external tools.

| Server | What It Does |
|--------|--------------|
| `github` | PRs, issues, code search |
| `jira` | Read/update tickets |
| `linear` | Issue tracking |
| `slack` | Team messaging |
| `sentry` | Error tracking |
| `postgres` | Database queries |

**Config:** `.mcp.json`

📚 **Docs:** `.claude/docs/MCP.md`

---

## 🤖 GitHub Actions

Automated Claude workflows.

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| PR Review | PR open, `@claude` | Auto code review |
| Docs Sync | Monthly | Keep docs updated |
| Code Quality | Weekly | Find quality issues |
| Dependency Audit | Biweekly | Update deps safely |

**Setup:** Add `ANTHROPIC_API_KEY` to repo secrets

📚 **Docs:** `.claude/docs/GITHUB-ACTIONS.md`

---

*Last updated: Run `/doc QUICK-REFERENCE.md` to regenerate*
