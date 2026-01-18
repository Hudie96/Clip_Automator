# Feature Planning Mode

You are now in **planning mode**. Do NOT write any code yet.

## Instructions

When planning a new feature or task:

### Step 1: Understand the Request
- Restate the goal in your own words
- Identify ambiguities and ask clarifying questions
- Define what "done" looks like

### Step 2: Research
- Read relevant existing code
- Check for similar patterns in the codebase
- Identify dependencies and potential conflicts

### Step 3: Create the Plan

Output a structured plan with:

```markdown
## 📋 Feature Plan: [Name]

### Goal
[One sentence description]

### Scope
- ✅ In scope: [list]
- ❌ Out of scope: [list]

### Technical Approach
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Files to Modify
- `path/to/file.ts` — [what changes]
- `path/to/another.ts` — [what changes]

### New Files to Create
- `path/to/new.ts` — [purpose]

### Tests Required
- [ ] Unit test for [X]
- [ ] Integration test for [Y]

### Dependencies
- [ ] Requires: [dependency]
- [ ] Blocked by: [nothing / issue #X]

### Risks & Mitigations
- Risk: [description] → Mitigation: [approach]

### Open Questions
1. [Question that needs answering]
```

### Step 4: Get Approval
- Present the plan
- Wait for user confirmation before implementing
- Adjust based on feedback

## Arguments

$ARGUMENTS — Description of the feature or task to plan

## Example Usage

```
/plan Add user authentication with email/password and OAuth
/plan Refactor the payment processing module
/plan Fix the memory leak in the data fetcher
```

---

**Remember:** Planning prevents rework. A good plan saves 10x the implementation time.
