# 📤 PR

Generate pull request description.

$ARGUMENTS

## Workflow

1. **Analyze changes**
   - What files changed?
   - What's the diff against base?
   - Categorize changes

2. **Determine PR type**
   - Feature, bugfix, refactor, docs, chore?

3. **Generate description**
   - Summary
   - What changed
   - How to test
   - Screenshots if UI changes

4. **Checklist**
   - Standard PR checklist items

## Output Format

```markdown
## Summary
[One paragraph explaining what this PR does and why]

## Type
- [ ] 🚀 Feature
- [ ] 🐛 Bugfix
- [ ] 🔧 Refactor
- [ ] 📚 Documentation
- [ ] 🏗️ Chore

## Changes
### Added
- [new things]

### Changed
- [modified things]

### Removed
- [deleted things]

## How to Test
1. [step]
2. [step]
3. [expected result]

## Screenshots
[If applicable]

## Checklist
- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] No console.logs/debug code
- [ ] Reviewed my own code

## Related Issues
Closes #[issue]
```

## Usage

- `/pr` — Generate for current branch
- `/pr against main` — Compare to specific base
- `/pr --verbose` — More detailed description
