# 🪝 Hooks Documentation

Hooks are scripts that run automatically before or after Claude takes actions.

## Hook Events

| Event | When It Fires | Can Block? | Use Cases |
|-------|---------------|------------|-----------|
| `PreToolUse` | Before a tool runs | ✅ Yes | Block dangerous commands, validate edits |
| `PostToolUse` | After a tool completes | ❌ No | Auto-format, run tests, lint |
| `UserPromptSubmit` | When you send a message | ❌ No | Add context, suggest skills |
| `SessionStart` | When Claude session begins | ❌ No | Show project info, set environment |
| `Stop` | When Claude finishes | ❌ No | Notifications, cleanup |

## Current Hooks in This Project

### PreToolUse Hooks

#### 1. Branch Protection
**Matcher:** `Edit|Write`
**Purpose:** Prevents edits on main/master branch

If you try to edit files on the main branch, you'll see:
```
🚫 Cannot edit on main/master. Create a feature branch first.
```

#### 2. Dangerous Command Blocker
**Matcher:** `Bash`
**Purpose:** Blocks potentially destructive commands

Blocked patterns:
- `rm -rf /` or `rm -rf ~`
- `sudo rm`
- `chmod 777`
- `> /dev/*`

### PostToolUse Hooks

#### 1. Auto-Format
**Matcher:** `Write|Edit`
**Purpose:** Automatically formats code after changes

| File Type | Formatter |
|-----------|-----------|
| JS/TS/JSON/CSS/MD | Prettier |
| Python | Black or Ruff |
| Go | gofmt |
| Rust | rustfmt |

#### 2. Test File Notification
**Matcher:** `Write|Edit`
**Purpose:** Reminds you to run tests when test files change

### SessionStart Hooks

#### Project Info
Shows current project and branch on session start:
```
📂 my-project | 🌿 feature/new-feature | Type /help for commands
```

## Hook Response Format

Hooks communicate via JSON to stdout:

```json
{
  "block": true,           // Block the action (PreToolUse only)
  "message": "Reason",     // Message shown to user when blocking
  "feedback": "Info",      // Non-blocking feedback message
  "suppressOutput": true,  // Hide command output
  "continue": false        // Whether Claude should continue
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `2` | Blocking error (PreToolUse) - stops the action |
| Other | Non-blocking error - shows warning but continues |

## Environment Variables Available

| Variable | Description |
|----------|-------------|
| `CLAUDE_USER_PROMPT` | The user's current prompt |
| `CLAUDE_TOOL_INPUT_FILE_PATH` | File being edited (Edit/Write) |
| `CLAUDE_TOOL_INPUT_COMMAND` | Command being run (Bash) |
| `CLAUDE_PROJECT_DIR` | Project root directory |

## Adding Custom Hooks

### 1. Add to settings.json

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### 2. Matcher Patterns

- `Edit` — File edits
- `Write` — New file creation
- `Bash` — Shell commands
- `Edit|Write` — Either (OR)
- `Bash(npm *)` — Specific commands

### 3. Example: Custom Linter

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_TOOL_INPUT_FILE_PATH\" == *.ts ]]; then npx eslint --fix \"$CLAUDE_TOOL_INPUT_FILE_PATH\"; fi",
      "timeout": 30
    }
  ]
}
```

## Skill Evaluation Hook

This project includes a smart skill suggestion system.

**Location:** `.claude/hooks/skill-eval.sh` and `skill-eval.js`

**How it works:**
1. Analyzes your prompt for keywords and patterns
2. Matches against rules in `skill-rules.json`
3. Suggests relevant skills based on confidence score

**Example output:**
```
💡 SKILL SUGGESTIONS

📁 Detected files: src/components/UserForm.tsx

Recommended skills:
1. form-patterns (HIGH)
   Matched: keyword "form", path pattern
2. react-patterns (MEDIUM)
   Matched: directory match, keyword "component"
```

**To customize:** Edit `.claude/hooks/skill-rules.json`

## Troubleshooting

### Hook Not Running
1. Check `matcher` pattern matches the tool
2. Verify script is executable: `chmod +x script.sh`
3. Check for syntax errors in settings.json

### Hook Blocking Unexpectedly
1. Check exit code — `exit 2` blocks in PreToolUse
2. Look for `{"block": true}` in output

### Hook Too Slow
1. Increase `timeout` value
2. Add early exit conditions
3. Run expensive operations asynchronously
