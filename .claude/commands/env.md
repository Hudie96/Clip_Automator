# ⚙️ Env

Help with environment setup.

$ARGUMENTS

## Workflow

1. **Assess current state**
   - What's installed?
   - What's configured?
   - What's missing?

2. **Identify gaps**
   - Missing tools
   - Wrong versions
   - Missing config

3. **Guide setup**
   - Step-by-step instructions
   - Verify each step

## Output Format

```
## ⚙️ Environment Setup

### 📊 Current State
| Requirement | Status | Version |
|-------------|--------|---------|
| Node | ✅ | 18.0.0 |
| npm | ✅ | 9.0.0 |
| Database | ❌ | Missing |

### 🔧 Required Actions
1. **[Action]**
   \`\`\`bash
   [command]
   \`\`\`

2. **[Action]**
   \`\`\`bash
   [command]
   \`\`\`

### 📋 Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `VAR_NAME` | ✅ | [what it's for] |

### 🧪 Verify Setup
\`\`\`bash
[verification command]
\`\`\`

Expected output: [what success looks like]
```

## Common Tasks

| Command | What It Does |
|---------|--------------|
| `/env` | Full environment check |
| `/env check` | Verify everything works |
| `/env vars` | List needed env variables |
| `/env setup [tool]` | Setup specific tool |
| `/env doctor` | Diagnose issues |

## Usage

- `/env` — Check what's needed
- `/env check` — Verify setup is correct
- `/env vars` — Show required variables
- `/env setup postgres` — Help setup specific tool
