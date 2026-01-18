# 📋 Changelog

Generate changelog for:

$ARGUMENTS

## Workflow

1. **Determine range**
   - Last release to now?
   - Specific commits?
   - Date range?

2. **Analyze commits**
   - Group by type
   - Extract meaningful changes
   - Identify breaking changes

3. **Generate formatted changelog**
   - Follow Keep a Changelog format
   - Highlight important changes

## Output Format

```markdown
## [Version] - YYYY-MM-DD

### 🚀 Added
- New feature description (#PR)

### 🔄 Changed
- Change description (#PR)

### 🐛 Fixed
- Bug fix description (#PR)

### 🗑️ Deprecated
- Deprecated feature (#PR)

### ❌ Removed
- Removed feature (#PR)

### 🔒 Security
- Security fix description (#PR)

### ⚠️ Breaking Changes
- Breaking change with migration path (#PR)
```

## Commit Type Mapping

| Prefix | Category |
|--------|----------|
| `feat:` | 🚀 Added |
| `fix:` | 🐛 Fixed |
| `docs:` | 📚 Documentation |
| `refactor:` | 🔄 Changed |
| `perf:` | ⚡ Performance |
| `test:` | 🧪 Testing |
| `chore:` | 🏗️ Maintenance |
| `BREAKING:` | ⚠️ Breaking |

## Usage

- `/changelog` — Since last tag
- `/changelog v1.0.0..v1.1.0` — Specific range
- `/changelog --since "2024-01-01"` — Since date
- `/changelog --breaking-only` — Just breaking changes
