# Universal .claude Directory Template

A comprehensive, production-ready template for configuring Claude Code in any project.

## Quick Start

1. **Copy to your project:**
   ```bash
   cp -r .claude /path/to/your/project/
   cp CLAUDE.md /path/to/your/project/
   ```

2. **Customize CLAUDE.md** with your project details

3. **Run the brainstorm skill** to further customize:
   ```
   claude
   > Use the brainstorm skill to help me configure this project
   ```

## Structure

```
.claude/
├── CLAUDE.md                # Project memory (customize this!)
├── settings.json            # Hooks and permissions
├── settings.local.json      # Personal overrides (gitignored)
├── .gitignore               # Ignore local files
│
├── commands/                # Slash commands
│   ├── plan.md              # /plan - Feature planning
│   ├── review.md            # /review - Code review
│   ├── test.md              # /test - Test generation
│   ├── debug.md             # /debug - Debugging workflow
│   ├── commit.md            # /commit - Pre-commit validation
│   ├── catchup.md           # /catchup - Reload context
│   └── handoff.md           # /handoff - Session notes
│
├── skills/
│   └── brainstorm/
│       └── SKILL.md         # Interactive configuration agent
│
├── rules/                   # Reference documentation
│   ├── api-design.md        # API patterns
│   ├── testing.md           # Test standards
│   ├── error-handling.md    # Error patterns
│   ├── git-workflow.md      # Git conventions
│   └── database.md          # Database patterns
│
├── hooks/                   # Hook scripts (optional)
│   └── (your scripts)
│
└── agents/                  # Sub-agent configs (optional)
    └── (your agents)
```

## Commands

| Command | Purpose |
|---------|---------|
| `/plan <feature>` | Create a plan before coding |
| `/review [files]` | Code review checklist |
| `/test <target>` | Generate tests |
| `/debug <issue>` | Systematic debugging |
| `/commit [msg]` | Pre-commit validation |
| `/catchup` | Reload context after /clear |
| `/handoff` | Write session notes |

## Customization

### 1. Update CLAUDE.md

Replace placeholder sections:
- Project description
- Tech stack
- Directory structure
- Build commands
- Project-specific rules

### 2. Adjust Settings

Edit `.claude/settings.json`:
- Update `allowedTools` for your stack
- Add framework-specific hooks
- Configure permissions

### 3. Create Custom Commands

Add `.md` files to `.claude/commands/`:
```markdown
# My Custom Command

$ARGUMENTS — What the user provides

Instructions for Claude...
```

### 4. Add Project Rules

Add `.md` files to `.claude/rules/`:
- Domain-specific patterns
- Team conventions
- Architecture decisions

### 5. Create Skills

Add folders to `.claude/skills/`:
```
my-skill/
├── SKILL.md       # Instructions and metadata
├── scripts/       # Helper scripts
└── templates/     # Reference templates
```

## Best Practices

1. **Keep CLAUDE.md under 200 lines** — Use @imports for details
2. **Be specific, not generic** — Actual commands, not placeholders
3. **Update as you learn** — Add rules when Claude makes mistakes
4. **Use the # key** — Quick-add to CLAUDE.md during sessions
5. **Commit .claude/** — Share configuration with your team

## Files NOT to Commit

- `.claude/settings.local.json` — Personal preferences
- `SCRATCHPAD.md` — Temporary work
- `HANDOFF.md` — Session-specific (or commit if useful)

## Troubleshooting

**Commands not appearing?**
- Check file is in `.claude/commands/`
- Restart Claude Code

**Hooks not running?**
- Check `settings.json` syntax
- Run `claude --debug`

**Claude ignoring rules?**
- Ensure CLAUDE.md is in project root
- Check @imports are valid paths
- Rules too long? Condense them.

---

Created with ❤️ for the Claude Code community.
