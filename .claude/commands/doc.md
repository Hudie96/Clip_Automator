# 📚 Doc

Generate documentation for:

$ARGUMENTS

## Workflow

1. **Identify target**
   - File, function, module, API, or project?
   - What type of docs needed?

2. **Analyze code**
   - What does it do?
   - What are the inputs/outputs?
   - What are the edge cases?

3. **Generate appropriate docs**
   - Match project's doc style
   - Include examples
   - Note gotchas

## Output Formats

### For Functions/Methods
```markdown
## functionName

[Brief description]

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | `type` | ✅ | [description] |
| param2 | `type` | ❌ | [description] |

### Returns
`type` — [description]

### Example
\`\`\`javascript
const result = functionName(arg1, arg2);
\`\`\`

### Throws
- `ErrorType` — [when this happens]

### Notes
- [important things to know]
```

### For Modules/Files
```markdown
## ModuleName

[What this module does]

### Exports
| Export | Type | Description |
|--------|------|-------------|
| thing1 | function | [desc] |
| thing2 | constant | [desc] |

### Usage
\`\`\`javascript
import { thing1 } from './module';
\`\`\`

### Dependencies
- [what this depends on]

### Related
- [related modules]
```

### For APIs
```markdown
## Endpoint Name

`METHOD /path/:param`

[Description]

### Parameters
| Name | In | Type | Required | Description |
|------|-----|------|----------|-------------|
| param | path | string | ✅ | [desc] |

### Request Body
\`\`\`json
{
  "field": "type"
}
\`\`\`

### Response
\`\`\`json
{
  "field": "type"
}
\`\`\`

### Errors
| Code | Description |
|------|-------------|
| 400 | [when] |
| 404 | [when] |
```

## Usage

- `/doc [function name]`
- `/doc [file path]`
- `/doc api [endpoint]`
- `/doc readme` — Generate/update README
- `/doc --inline` — Add JSDoc/docstrings to code
