# The Three-Step Agentic Loop

This document describes the agentic architecture powering this template.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        THE AGENTIC LOOP ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────────┐
     │  1. GATHER CONTEXT  │
     │  & RESEARCH         │
     │                     │
     │  • Agentic search   │
     │  • Read files       │
     │  • Plan steps       │
     └──────────┬──────────┘
                │
                ▼
     ┌─────────────────────┐
     │  2. AUTONOMOUS      │
     │  ACTION             │
     │                     │
     │  • Execute tasks    │
     │  • Write code       │
     │  • Run commands     │
     └──────────┬──────────┘
                │
                ▼
     ┌─────────────────────┐
     │  3. VERIFICATION &  │
     │  SELF-CORRECTION    │
     │                     │
     │  • Run checks       │
     │  • Fix issues       │
     │  • Report results   │
     └──────────┬──────────┘
                │
         ┌──────┴──────┐
         │             │
       Pass          Fail
         │             │
         ▼             ▼
      Complete    Loop back
                  to step 2
```

## The Architecture Components

### 1. Model Context Protocol (MCP)

**Purpose:** Connect to external tools and services

**Configured Servers:**
| Server | Purpose |
|--------|---------|
| github | GitHub API (issues, PRs, repos) |
| filesystem | Enhanced file operations |
| memory | Persistent context across sessions |
| fetch | HTTP requests to external APIs |
| sequential-thinking | Step-by-step reasoning |

**Adding More:**
- Slack for team communication
- PostgreSQL/SQLite for database access
- Puppeteer for browser automation
- Custom servers for project-specific tools

**File:** `.mcp.json`

### 2. Claude Model Performance

**Available Models:**

| Model | Best For | Context | Tool Use |
|-------|----------|---------|----------|
| **Opus 4.5** | Complex planning, security, architecture | 1M+ tokens | High accuracy |
| **Sonnet 4.5** | Standard coding, most tasks | 1M tokens | Fast, reliable |
| **Haiku** | Quick checks, validation | 200K tokens | Very fast |

**Model Selection Rules:**
- Security tasks → Always Opus
- Standard coding → Sonnet
- Simple validation → Haiku
- Unknown complexity → Start Sonnet, escalate if needed

**File:** `.claude/rules/model-selection.md`

### 3. Specialized Subagents

**Purpose:** Delegate smaller tasks to parallel sub-agents for faster execution

**Available Agents:**
| Agent | Specialty | Default Model |
|-------|-----------|---------------|
| code-reviewer | Code quality, best practices | Sonnet |
| bug-hunter | Finding bugs, edge cases | Sonnet |
| test-generator | Creating tests | Sonnet |
| doc-writer | Documentation | Sonnet |
| refactor-bot | Code cleanup | Sonnet |
| security-scanner | Vulnerabilities | Opus |
| **master** | Orchestrates all agents | Opus |

**Parallel Execution:**
- Independent modules → Run in parallel
- Dependent tasks → Run sequentially
- Mixed workflows → Parallel groups, then sequential combine

**Files:** `.claude/agents/*.md`

### 4. Long-Context Engineering

**Purpose:** Ground agents in project-specific rules using 1M+ token context

**Context Files:**
| File | Purpose | Priority |
|------|---------|----------|
| `CLAUDE.md` | Project memory, quick reference | High |
| `.claude/rules/*.md` | Coding standards, patterns | Medium |
| `.claude/commands/*.md` | Slash commands | Medium |
| `.claude/skills/*.md` | AI skills | Medium |
| `.claude/agents/*.md` | Agent definitions | High |

**Token Optimization:**
- `.claudeignore` excludes large files (node_modules, .git, etc.)
- Smart model selection reduces costs
- Parallel execution speeds up complex tasks

**Command:** `/tokens` to analyze and optimize

## The Loop in Detail

### Step 1: Gather Context & Research

**What happens:**
- Parse user request
- Search codebase (grep, glob, read)
- Identify relevant files
- Plan implementation steps

**Tools used:**
- Glob, Grep, Read for file search
- MCP servers for external data
- sequential-thinking for planning

**Model selection:**
- Planning: Opus (complex) or Sonnet (standard)
- File search: Haiku (fast, cheap)

### Step 2: Autonomous Action

**What happens:**
- Execute the plan
- Write/edit code
- Run bash commands
- Use computer tools if needed

**Tools used:**
- Edit, Write for file changes
- Bash for commands
- MCP tools for external actions

**Hooks applied:**
- PreToolUse: Block dangerous commands, branch protection
- PostToolUse: Auto-format, lint, type check

**Model selection:**
- Execution: Sonnet (most tasks)
- Critical code: Opus (security, architecture)

### Step 3: Verification & Self-Correction

**What happens:**
- Run automated checks
- Identify issues
- Self-correct if possible
- Report results

**Checks run:**
- TypeScript compilation
- ESLint/linting
- Test suite
- Build verification

**Self-correction rules:**
- Max 3 attempts per issue
- Fix one thing at a time
- Escalate if stuck

**Model selection:**
- Validation: Haiku (fast, cheap)
- Complex fixes: Sonnet
- Security fixes: Opus

## Hooks System

**Purpose:** Automate actions before/after tool use

| Hook | When | Purpose |
|------|------|---------|
| PreToolUse | Before action | Block dangerous commands |
| PostToolUse | After action | Auto-format, lint, notify |
| SessionStart | Session begins | Show project info |
| Stop | Session ends | Cleanup |

**Current Hooks:**
- Branch protection (no edits on main)
- Dangerous command blocker
- Auto-format (Prettier, Black, etc.)
- TypeScript check on save
- ESLint on save
- Test file notifications

**File:** `.claude/settings.json`

## Parallel Execution Patterns

### Pattern 1: Multi-Module Audit

```
┌──────────────┬──────────────┬──────────────┐
│ src/api/     │ src/auth/    │ src/utils/   │
│ bug-hunter   │ bug-hunter   │ bug-hunter   │
│ sec-scanner  │ sec-scanner  │ sec-scanner  │
└──────────────┴──────────────┴──────────────┘
              ↓ combine findings ↓
           code-reviewer (all)
```

### Pattern 2: Pre-filter with Haiku

```
Step 1 (Haiku):   Categorize all files
                  ↓
Step 2 (Sonnet):  Process standard files
Step 2 (Opus):    Process security files  } parallel
                  ↓
Step 3 (Haiku):   Validate all changes
```

### Pattern 3: Mixed Sequential + Parallel

```
Step 1: bug-hunter (find issues)
           ↓
Step 2: ┌──────────────┬──────────────┐
        │ doc-writer   │ test-gen     │ } parallel
        └──────────────┴──────────────┘
           ↓
Step 3: code-reviewer (final)
```

## Cost Optimization

### Model Costs (Approximate)

| Model | Input | Output |
|-------|-------|--------|
| Opus 4.5 | $15/M tokens | $75/M tokens |
| Sonnet 4.5 | $3/M tokens | $15/M tokens |
| Haiku | $0.25/M tokens | $1.25/M tokens |

### Optimization Strategies

1. **Use Haiku for quick tasks** — 60x cheaper than Opus
2. **Parallel execution** — Faster completion, same cost
3. **Smart context** — .claudeignore reduces input tokens
4. **Model escalation** — Start cheap, escalate only when needed

### Example Savings

```
Task: Full audit of 3 modules

All Opus:       ~$8.00
Smart routing:  ~$2.50 (70% savings)

Breakdown:
- Haiku: File categorization, validation
- Sonnet: Bug hunting, test generation, docs
- Opus: Security scanning only
```

## Quick Reference

### Commands

| Command | Purpose |
|---------|---------|
| `/agent` | Run master agent for complex tasks |
| `/verify` | Run verification checks |
| `/tokens` | Analyze token usage and costs |
| `/plan` | Enter planning mode |

### Files to Know

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project memory |
| `.mcp.json` | MCP server config |
| `.claude/settings.json` | Hooks and permissions |
| `.claudeignore` | Files to skip |

### Agent Invocation

```
/agent [task]              — Let master agent decide
/agent security audit      — Focus on security
/agent full audit          — All agents
/agent fix and verify      — Bug hunter + tests + review
```

---

*The agentic loop is designed for autonomous, efficient, and verifiable code changes.*
