# Error Handling Standards

## Principles

1. **Fail fast** — Catch errors early, at the boundary
2. **Fail loud** — Don't swallow errors silently
3. **Fail gracefully** — Users should see helpful messages

## Error Types

### Custom Error Classes
```typescript
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message: string, public fields: Record<string, string>) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 'UNAUTHORIZED', 401);
  }
}
```

## Error Handling Patterns

### Try-Catch at Boundaries
```typescript
// API route handler
async function handler(req, res) {
  try {
    const result = await businessLogic();
    res.json({ data: result });
  } catch (error) {
    handleError(error, res);
  }
}
```

### Centralized Error Handler
```typescript
function handleError(error: unknown, res: Response) {
  if (error instanceof AppError) {
    logger.warn(error.message, { code: error.code });
    return res.status(error.statusCode).json({
      error: {
        code: error.code,
        message: error.message
      }
    });
  }
  
  // Unknown error - log and return generic message
  logger.error('Unexpected error', { error });
  return res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
}
```

### Async/Await Error Handling
```typescript
// Use try-catch for expected errors
try {
  const user = await db.users.findUnique({ where: { id } });
  if (!user) throw new NotFoundError('User');
} catch (error) {
  // Handle specific errors
}

// Use .catch() for fire-and-forget
sendEmail(user.email).catch(error => {
  logger.error('Failed to send email', { error, userId: user.id });
});
```

## Logging Standards

### What to Log
- Error message and code
- Stack trace (in development)
- Request ID for correlation
- User ID (if authenticated)
- Relevant context

### What NOT to Log
- Passwords or secrets
- Full credit card numbers
- Personal data (GDPR)
- Session tokens

### Log Levels
```typescript
logger.debug('Query executed', { sql, params }); // Development only
logger.info('User logged in', { userId });        // Normal operations
logger.warn('Rate limit approaching', { ip });    // Potential issues
logger.error('Database connection failed', { error }); // Actual errors
```

## Circuit Breaker Pattern

For external service calls:
```typescript
const breaker = new CircuitBreaker(externalService, {
  failureThreshold: 5,
  resetTimeout: 30000
});

breaker.on('open', () => logger.warn('Circuit opened'));
breaker.on('halfOpen', () => logger.info('Circuit half-open'));
breaker.on('close', () => logger.info('Circuit closed'));
```

## Retry Pattern

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  delay = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(delay * Math.pow(2, i)); // Exponential backoff
    }
  }
  throw new Error('Unreachable');
}
```

## User-Facing Errors

- Use clear, non-technical language
- Suggest what the user can do
- Don't expose internal details
- Provide error codes for support

```typescript
// Bad
"ECONNREFUSED 127.0.0.1:5432"

// Good
"We're having trouble connecting. Please try again in a few moments. (Error: DB001)"
```

---

*Every error is an opportunity to help the user or fix a bug.*
