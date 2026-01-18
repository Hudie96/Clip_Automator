# Session Handoff Command

Create a handoff document before ending a session, for future you or teammates.

## Instructions

$ARGUMENTS — Optional: specific notes to include

### What to Document

Write a `HANDOFF.md` file with:

```markdown
# Session Handoff

**Date:** [timestamp]
**Branch:** [current branch]
**Session Focus:** [what was worked on]

## What Was Accomplished
- [x] [Completed task]
- [x] [Completed task]
- [ ] [In progress]

## Current State
[Brief description of where things stand]

## What Was Tried (and didn't work)
- Approach A: [why it failed]
- Approach B: [why it failed]

## Next Steps
1. [ ] [Immediate next task]
2. [ ] [Following task]
3. [ ] [Future consideration]

## Key Decisions Made
- Decision: [what was decided]
  - Reason: [why]
  - Trade-offs: [what was sacrificed]

## Files Modified
- `path/to/file.ts` — [what changed]

## Open Questions
- [ ] [Question needing answer]
- [ ] [Uncertainty to resolve]

## Context for Next Session
[Anything the next person (or future you) needs to know]

## Commands to Run
```bash
# To continue this work:
git checkout [branch]
npm install
npm run dev
```
```

### Best Practices

1. **Be specific** — Future you won't remember vague notes
2. **Include failures** — What didn't work is valuable
3. **List next steps** — Make it easy to pick up
4. **Note blockers** — What's preventing progress

### Output Location

Save to project root:
```bash
# Update existing or create new
echo "[content]" > HANDOFF.md
git add HANDOFF.md
```

## Example Usage

```
/handoff                              # Generate from session history
/handoff "blocked on API key"         # Add specific note
/handoff --commit                     # Also commit the handoff
```

---

**Your future self will thank you.**
