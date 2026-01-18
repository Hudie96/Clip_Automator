# Model Selection Strategy

Use the right model for each task to balance cost, speed, and quality.

## Model Tiers

| Model | Best For | Context | Cost | Speed |
|-------|----------|---------|------|-------|
| **Opus 4.5** | Complex planning, architecture, critical decisions | 1M+ tokens | $$$ | Slower |
| **Sonnet 4.5** | General coding, execution, most tasks | 1M tokens | $$ | Fast |
| **Haiku** | Quick queries, simple tasks, validation | 200K tokens | $ | Very fast |

## When to Use Each Model

### Opus 4.5 (Complex/Critical)

Use for:
- Architectural decisions
- Complex multi-step planning
- Security audits
- Production-ready reviews
- Debugging tricky issues
- Code that handles money, auth, or sensitive data

```
Task: "Design the authentication system"
Model: Opus 4.5
Reason: Architectural decision with security implications
```

### Sonnet 4.5 (Default/Execution)

Use for:
- Writing new features
- Refactoring code
- Code reviews
- Test generation
- Documentation
- Most everyday tasks

```
Task: "Add a user profile page"
Model: Sonnet 4.5
Reason: Standard feature implementation
```

### Haiku (Quick/Simple)

Use for:
- Syntax questions
- Simple explanations
- Quick lookups
- Formatting checks
- File existence checks
- Simple string operations

```
Task: "What's the syntax for async/await?"
Model: Haiku
Reason: Simple knowledge lookup
```

## Task-to-Model Mapping

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| `/plan` | Opus | Planning needs deep thinking |
| `/agent full audit` | Opus | Critical quality gate |
| `/review` (security) | Opus | Security requires thoroughness |
| `/build` | Sonnet | Standard execution |
| `/test` | Sonnet | Test generation is well-defined |
| `/fix` | Sonnet | Bug fixes are typically focused |
| `/refactor` | Sonnet | Structured transformation |
| `/explain` | Sonnet | Clear explanation task |
| `/help` | Haiku | Quick assistance |
| `/search` | Haiku | Information retrieval |
| `/stuck` | Haiku first | Try quick help, escalate if needed |
| Syntax check | Haiku | Trivial verification |

## Agent Model Assignment

| Agent | Default Model | Escalate To |
|-------|---------------|-------------|
| bug-hunter | Sonnet | Opus (critical bugs) |
| security-scanner | Opus | — |
| test-generator | Sonnet | — |
| doc-writer | Sonnet | — |
| refactor-bot | Sonnet | — |
| code-reviewer | Sonnet | Opus (production code) |
| master | Opus | — |

## Escalation Rules

Start cheap, escalate when needed:

```
1. Haiku: "Is this file a test file?" → Quick check

2. If complex: Escalate to Sonnet
   "This test file has mocking issues" → Needs understanding

3. If critical: Escalate to Opus
   "The auth tests are failing randomly" → Security + complexity
```

## Cost Optimization Patterns

### Pattern 1: Pre-filter with Haiku

```
Task: "Review all changed files"

Step 1 (Haiku): List and categorize files by complexity
Step 2 (Sonnet): Review standard files
Step 3 (Opus): Review security-critical files only
```

### Pattern 2: Validate with Haiku

```
Task: "Refactor this module"

Step 1 (Sonnet): Perform refactoring
Step 2 (Haiku): Quick syntax/import check
Step 3 (Haiku): Verify all exports still work
```

### Pattern 3: Explore with Haiku, Execute with Sonnet

```
Task: "Add caching to slow endpoints"

Step 1 (Haiku): Find slow endpoints (search/grep)
Step 2 (Haiku): Check existing caching patterns
Step 3 (Sonnet): Implement caching
```

## Subagent Parallelization by Model

When running parallel subagents, group by model to optimize:

```
Parallel Group A (Haiku):
├── File categorization
├── Import validation
└── Syntax checks

Parallel Group B (Sonnet):
├── bug-hunter on module 1
├── bug-hunter on module 2
└── test-generator on module 3

Sequential (Opus):
└── security-scanner on auth module
```

## Cost Monitoring

Track model usage to optimize:

```markdown
## Session Cost Estimate

| Model | Calls | ~Tokens | ~Cost |
|-------|-------|---------|-------|
| Opus | 2 | 50K | $1.50 |
| Sonnet | 15 | 200K | $1.20 |
| Haiku | 30 | 100K | $0.05 |
| **Total** | 47 | 350K | **$2.75** |

Savings vs. all-Opus: ~70%
```

## Decision Flowchart

```
Is it a simple lookup/check?
├── Yes → Haiku
└── No ↓

Is it security-critical or architectural?
├── Yes → Opus
└── No ↓

Is it complex multi-step reasoning?
├── Yes → Opus
└── No → Sonnet
```

---

*Use the cheapest model that can do the job well. Escalate, don't over-engineer.*
