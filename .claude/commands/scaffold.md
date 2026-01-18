# 🏭 Scaffold

Generate boilerplate for:

$ARGUMENTS

## Workflow

1. **Identify what to scaffold**
   - Component? Module? Feature? File?
   - What patterns does this project use?

2. **Check project conventions**
   - Look at existing similar code
   - Match naming patterns
   - Use same structure

3. **Generate with proper structure**
   - Follow project's established patterns
   - Include standard imports
   - Add placeholder comments

4. **Report what was created**
   - List files
   - Explain structure
   - Note what needs filling in

## Output Format

```
## 🏭 Scaffolded: [thing]

### 📁 Files Created
- `[path]` — [purpose]
- `[path]` — [purpose]

### 📋 Structure
[Brief explanation of the scaffold]

### ✏️ TODO
- [ ] [what needs to be filled in]
- [ ] [what needs to be customized]
```

## Common Scaffolds

| Type | What It Creates |
|------|-----------------|
| `component` | UI component with standard structure |
| `module` | Feature module with exports |
| `api` | API endpoint/route |
| `test` | Test file with setup |
| `hook` | Custom hook template |
| `service` | Service class/module |
| `model` | Data model/type |

## Usage

- `/scaffold component UserProfile`
- `/scaffold api /users/:id`
- `/scaffold test for auth module`
- `/scaffold feature checkout flow`
