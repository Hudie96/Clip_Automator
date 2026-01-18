# Test Generation Command

Generate comprehensive tests for the specified code.

## Instructions

$ARGUMENTS — File path, function name, or feature to test

### Step 1: Analyze the Code
- Read the target code thoroughly
- Identify all code paths and branches
- Note dependencies and mocks needed
- Check existing test patterns in the project

### Step 2: Plan Test Cases

Create tests for:

#### Happy Path
- Normal expected usage
- Valid inputs producing expected outputs

#### Edge Cases
- Empty inputs, null values
- Boundary conditions (0, -1, MAX_INT)
- Single item vs multiple items

#### Error Cases
- Invalid inputs
- Network failures
- Timeout scenarios
- Permission errors

#### Integration Points
- API calls
- Database operations
- External service interactions

### Step 3: Generate Tests

Follow the project's testing patterns. Use this structure:

```typescript
describe('[Component/Function Name]', () => {
  // Setup
  beforeEach(() => {
    // Common setup
  });

  describe('[method or scenario]', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      const input = ...;
      
      // Act
      const result = functionUnderTest(input);
      
      // Assert
      expect(result).toBe(expected);
    });

    it('should throw error when [invalid condition]', () => {
      expect(() => functionUnderTest(invalidInput))
        .toThrow(ExpectedError);
    });
  });
});
```

### Step 4: Verify

After generating tests:
1. Run the test suite to verify they pass
2. Check coverage metrics
3. Identify any uncovered paths

### Output Format

```markdown
## 🧪 Tests Generated for: [target]

### Test File: [path]

### Coverage Summary
- Statements: X%
- Branches: X%
- Functions: X%
- Lines: X%

### Test Cases Created
1. ✅ [test name] — [what it verifies]
2. ✅ [test name] — [what it verifies]
...

### Mocks Required
- [dependency] — [why mocked]

### Run Command
`npm test -- [test file]`
```

## TDD Mode

If implementing a new feature, write tests FIRST:

1. Write a failing test (Red)
2. Implement minimal code to pass (Green)
3. Refactor while keeping tests green (Refactor)

## Example Usage

```
/test src/utils/formatDate.ts          # Test specific file
/test UserService.createUser           # Test specific function
/test authentication flow              # Test feature area
/test --tdd new payment processor      # TDD mode for new code
```

---

**Good tests document behavior and catch regressions.**
