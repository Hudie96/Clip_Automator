# 🎫 Ticket

Work on a ticket from your issue tracker (JIRA, Linear, GitHub Issues).

$ARGUMENTS

## Prerequisites

This command works best with MCP servers configured:
- JIRA: `@anthropic/mcp-jira`
- Linear: `@anthropic/mcp-linear`
- GitHub: `@modelcontextprotocol/server-github`

Without MCP, provide ticket details manually.

## Workflow

### Phase 1: Understand the Ticket

```
🎫 TICKET ANALYSIS

**ID:** [ticket ID]
**Title:** [ticket title]
**Status:** [current status]

**Description:**
[ticket description]

**Acceptance Criteria:**
- [ ] [criterion 1]
- [ ] [criterion 2]

**Linked Items:**
- [related tickets, PRs, docs]
```

### Phase 2: Plan Implementation

```
📋 IMPLEMENTATION PLAN

**Affected Files:**
- [file 1] — [what changes]
- [file 2] — [what changes]

**Approach:**
1. [step 1]
2. [step 2]
3. [step 3]

**Risks:**
- [potential issues]

**Estimated Complexity:** [Low/Medium/High]

Proceed with implementation?
```

### Phase 3: Implement

1. Create feature branch
   ```bash
   git checkout -b feature/[ticket-id]-[short-description]
   ```

2. Implement changes incrementally
   - Make one logical change at a time
   - Verify each step works

3. Write/update tests

4. Update ticket status to "In Progress" (if MCP available)

### Phase 4: Complete

1. Run all checks
   ```bash
   npm test
   npm run lint
   npm run typecheck
   ```

2. Commit with ticket reference
   ```bash
   git commit -m "feat([scope]): [description]

   Resolves [TICKET-ID]"
   ```

3. Push and create PR
   ```bash
   git push origin HEAD
   gh pr create --title "[TICKET-ID] [Title]" --body "Resolves [TICKET-ID]"
   ```

4. Update ticket status to "In Review" (if MCP available)

5. Link PR to ticket

## Output Format

```
## 🎫 Ticket Complete: [TICKET-ID]

### ✅ Acceptance Criteria
- [x] [criterion 1]
- [x] [criterion 2]

### 📁 Changes Made
- [file]: [what changed]

### 🔗 Links
- PR: [PR link]
- Ticket: [ticket link]

### 🧪 Verification
- Tests: ✅ Passing
- Lint: ✅ Clean
- Types: ✅ Valid

### ⏭️ Next Steps
- [ ] Code review
- [ ] QA verification
```

## Usage

- `/ticket PROJ-123` — Work on specific ticket
- `/ticket` — Show tickets assigned to you (requires MCP)
- `/ticket create [title]` — Create new ticket (requires MCP)
