# 📦 Deps

Analyze project dependencies.

$ARGUMENTS

## Workflow

1. **Scan dependency files**
   - package.json, requirements.txt, etc.
   - Lock files for actual versions

2. **Analyze**
   - What's installed
   - Version status
   - Potential issues

3. **Report findings**
   - Outdated packages
   - Security concerns
   - Unused dependencies

## Output Format

```
## 📦 Dependencies Report

### 📊 Overview
| Metric | Count |
|--------|-------|
| Total deps | X |
| Dev deps | X |
| Outdated | X |
| Security issues | X |

### 🔴 Security Issues
| Package | Severity | Advisory |
|---------|----------|----------|
| pkg | HIGH | [description] |

### 🟡 Outdated
| Package | Current | Latest | Breaking? |
|---------|---------|--------|-----------|
| pkg | 1.0.0 | 2.0.0 | ⚠️ Yes |
| pkg | 1.0.0 | 1.1.0 | No |

### 🔵 Potentially Unused
| Package | Last Import Found |
|---------|-------------------|
| pkg | None found |

### ✅ Recommendations
1. [Prioritized actions]
```

## Options

| Command | What It Does |
|---------|--------------|
| `/deps` | Full analysis |
| `/deps outdated` | Just outdated packages |
| `/deps security` | Just security issues |
| `/deps unused` | Find unused deps |
| `/deps why [pkg]` | Why is this installed? |
| `/deps tree` | Dependency tree |

## Usage

- `/deps` — Full report
- `/deps outdated --major` — Just major updates
- `/deps security` — Security audit
- `/deps why lodash` — Why do we have this?
