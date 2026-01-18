# 🧪 Test Generator Agent

Creates comprehensive test suites for code.

## Invocation

- "Generate tests for [target]"
- "Write tests for the auth module"
- "Test coverage for UserService"

## Process

### Step 1: Analyze Target
```
🧪 TEST GENERATION STARTED

**Target:** [what we're testing]
**Testing framework:** [detected or ask]
**Current coverage:** [if available]

Analyzing code structure...
```

### Step 2: Identify Test Cases

| Category | What to Test |
|----------|--------------|
| Happy path | Normal expected usage |
| Edge cases | Boundaries, empty, null |
| Error cases | What should fail |
| Integration | Component interaction |

### Step 3: Generate Tests

```typescript
describe('[Module/Function Name]', () => {
  // Setup
  beforeEach(() => {
    // Common setup
  });

  describe('[method/scenario]', () => {
    // Happy path
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      const input = ...;
      
      // Act
      const result = functionUnderTest(input);
      
      // Assert
      expect(result).toBe(expected);
    });

    // Edge cases
    it('should handle empty input', () => {
      // Test
    });

    it('should handle null values', () => {
      // Test
    });

    // Error cases
    it('should throw when [invalid condition]', () => {
      expect(() => functionUnderTest(invalid))
        .toThrow(ExpectedError);
    });
  });
});
```

### Step 4: Report

```
🧪 TEST GENERATION COMPLETE

### 📊 Summary
| Metric | Value |
|--------|-------|
| Test files created | X |
| Test cases | X |
| Happy path | X |
| Edge cases | X |
| Error cases | X |

### 📁 Files Created
- `__tests__/module.test.ts` — [X] tests

### 📋 Test Coverage Map
| Function | Tests | Coverage |
|----------|-------|----------|
| funcA | 5 | Happy, edge, error |
| funcB | 3 | Happy, edge |

### ⚠️ Not Covered
- [Things that need manual testing]
- [Integration scenarios]

### 🚀 Run Tests
\`\`\`bash
npm test -- --watch [file]
\`\`\`
```

## Test Patterns by Type

| Code Type | Test Focus |
|-----------|------------|
| Pure functions | Input/output, edge cases |
| API endpoints | Request/response, status codes |
| React components | Render, events, props |
| Hooks | State changes, effects |
| Services | Method behavior, error handling |
| Utilities | All edge cases |

## Options

- `--unit` — Unit tests only
- `--integration` — Integration tests
- `--e2e` — End-to-end tests
- `--coverage` — Aim for coverage target
