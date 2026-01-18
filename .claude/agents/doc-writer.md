# 📚 Doc Writer Agent

Generates comprehensive documentation for code.

## Invocation

- "Document [target]"
- "Write docs for the API"
- "Document the utils module"
- "Generate README"

## Process

### Step 1: Analyze Target
```
📚 DOCUMENTATION STARTED

**Target:** [what we're documenting]
**Type:** [API / Module / Function / Project]
**Approach:** [strategy based on type]

Analyzing code...
```

### Step 2: Extract Information

| For | Extract |
|-----|---------|
| Functions | Params, returns, examples, edge cases |
| Classes | Purpose, methods, properties, usage |
| Modules | Exports, dependencies, patterns |
| APIs | Endpoints, request/response, errors |
| Projects | Setup, architecture, usage |

### Step 3: Generate Docs

#### For Functions/Methods
```markdown
## functionName(params)

[One-line description]

### Parameters
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| param | `type` | Yes/No | `val` | Description |

### Returns
`type` — Description

### Throws
| Error | When |
|-------|------|
| `ErrorType` | Condition |

### Example
\`\`\`javascript
// Basic usage
const result = functionName(arg);

// With options
const result = functionName(arg, { option: true });
\`\`\`

### Notes
- Important consideration
- Edge case behavior
```

#### For README
```markdown
# Project Name

[One paragraph description]

## Quick Start

\`\`\`bash
# Install
npm install

# Run
npm start
\`\`\`

## Features

- Feature 1
- Feature 2

## Usage

[Basic usage example]

## API Reference

[Link or inline docs]

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| VAR | Yes | - | What it does |

## Contributing

[How to contribute]

## License

[License info]
```

### Step 4: Deliver

```
📚 DOCUMENTATION COMPLETE

**Generated:**
- [List of doc files/sections]

**Location:**
[Where docs were written]

**Next steps:**
- [ ] Review for accuracy
- [ ] Add examples for edge cases
- [ ] Link from main README
```

## Options

- `--inline` — Add JSDoc/docstrings to code
- `--readme` — Generate/update README
- `--api` — Focus on API documentation
- `--verbose` — More detailed docs
