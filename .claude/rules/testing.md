# Testing Standards

## Test Structure

### File Organization
- Tests live alongside source: `Button.tsx` → `Button.test.tsx`
- Integration tests in `__tests__/integration/`
- E2E tests in `e2e/`

### Naming Convention
```typescript
describe('ComponentName', () => {
  describe('methodName', () => {
    it('should [expected behavior] when [condition]', () => {
      // ...
    });
  });
});
```

## Test Types

### Unit Tests
- Test single functions/components in isolation
- Mock all dependencies
- Fast execution (<100ms per test)

### Integration Tests
- Test multiple units working together
- Minimal mocking (real DB in test mode)
- Test API endpoints end-to-end

### E2E Tests
- Test full user flows
- Real browser, real backend
- Slower but high confidence

## Testing Patterns

### AAA Pattern
```typescript
it('should calculate total with tax', () => {
  // Arrange
  const items = [{ price: 100 }, { price: 50 }];
  const taxRate = 0.1;
  
  // Act
  const total = calculateTotal(items, taxRate);
  
  // Assert
  expect(total).toBe(165);
});
```

### What to Test

✅ **Do Test:**
- Business logic
- Edge cases
- Error handling
- User interactions
- API contracts

❌ **Don't Test:**
- Implementation details
- Third-party libraries
- Simple getters/setters
- Framework internals

## Mocking Guidelines

```typescript
// Mock external dependencies
jest.mock('./api', () => ({
  fetchUser: jest.fn()
}));

// Mock at the boundary
const mockFetch = jest.fn().mockResolvedValue({ data: user });

// Prefer dependency injection over global mocks
function createService(api = realApi) {
  return { getUser: () => api.fetchUser() };
}
```

## Test Coverage

Target coverage:
- Statements: 80%+
- Branches: 75%+
- Functions: 80%+

Focus on critical paths over hitting numbers.

## TDD Workflow

1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Clean up while keeping green

## Anti-Patterns

❌ **Test implementation, not behavior**
```typescript
// Bad: testing internal state
expect(component.state.isLoading).toBe(true);

// Good: testing observable behavior
expect(screen.getByText('Loading...')).toBeInTheDocument();
```

❌ **Flaky tests**
- Avoid `sleep()` — use proper async waiting
- Don't depend on test order
- Clean up after each test

❌ **Over-mocking**
- If you mock everything, you test nothing
- Prefer integration tests for complex flows

---

*Tests are documentation. Write them for the next developer.*
