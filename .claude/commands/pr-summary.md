# 📝 PR Summary

Generate a comprehensive pull request description.

$ARGUMENTS

## Workflow

### Step 1: Analyze Changes

```bash
# Get the diff
git diff origin/main...HEAD --stat
git diff origin/main...HEAD

# Get commit messages
git log origin/main...HEAD --oneline
```

### Step 2: Categorize Changes

- **Added**: New files, features, tests
- **Modified**: Changed behavior, refactors
- **Removed**: Deleted code, deprecated features
- **Fixed**: Bug fixes

### Step 3: Generate PR Description

```markdown
## Summary

[One paragraph explaining what this PR does and why]

## Type of Change

- [ ] 🚀 New feature
- [ ] 🐛 Bug fix
- [ ] 🔧 Refactor
- [ ] 📚 Documentation
- [ ] 🧪 Tests
- [ ] 🏗️ Infrastructure/CI

## Changes

### Added
- [New thing 1]
- [New thing 2]

### Changed
- [Changed thing 1]
- [Changed thing 2]

### Removed
- [Removed thing 1]

### Fixed
- [Bug fix 1]

## Testing

### How to Test
1. [Step 1]
2. [Step 2]
3. [Expected result]

### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots

[If applicable, add screenshots or recordings]

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests pass locally

## Related

- Closes #[issue]
- Related to #[issue]
- Depends on #[PR]

## Notes for Reviewers

[Any specific areas to focus on, concerns, or context]
```

## Options

| Flag | Effect |
|------|--------|
| `--short` | Brief summary only |
| `--detailed` | Include file-by-file breakdown |
| `--copy` | Copy to clipboard |
| `--create` | Create PR with this description |

## Usage

```bash
# Generate PR description
/pr-summary

# Generate and create PR
/pr-summary --create

# Short version
/pr-summary --short

# Compare against different base
/pr-summary against develop
```

## After Generation

The PR description is ready to:
1. Copy into GitHub/GitLab PR form
2. Use with `gh pr create --body "..."`
3. Pipe to clipboard: `| pbcopy` (macOS) or `| xclip` (Linux)
