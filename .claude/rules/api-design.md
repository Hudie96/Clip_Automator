# API Design Rules

## REST Conventions

### URL Structure
```
GET    /resources           # List all
GET    /resources/:id       # Get one
POST   /resources           # Create
PUT    /resources/:id       # Full update
PATCH  /resources/:id       # Partial update
DELETE /resources/:id       # Delete
```

### Naming
- Use plural nouns: `/users` not `/user`
- Use kebab-case: `/user-profiles` not `/userProfiles`
- Avoid verbs in URLs: `/users` not `/getUsers`
- Nest for relationships: `/users/:id/posts`

### Query Parameters
- Filtering: `?status=active&role=admin`
- Sorting: `?sort=created_at:desc`
- Pagination: `?page=2&limit=20` or `?cursor=abc123`
- Fields: `?fields=id,name,email`

## Request/Response Format

### Success Response
```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly message",
    "details": [
      { "field": "email", "message": "Invalid format" }
    ]
  }
}
```

### HTTP Status Codes
- `200` — Success
- `201` — Created
- `204` — No content (successful delete)
- `400` — Bad request (client error)
- `401` — Unauthorized (not logged in)
- `403` — Forbidden (logged in but not allowed)
- `404` — Not found
- `409` — Conflict (duplicate, etc.)
- `422` — Unprocessable (validation failed)
- `500` — Server error

## Validation

Always validate:
- Required fields
- Data types
- String lengths
- Number ranges
- Enum values
- Custom business rules

Return all validation errors at once, not one at a time.

## Authentication

- Use Bearer tokens in Authorization header
- Include user ID in JWT payload
- Set appropriate expiration
- Implement refresh token flow

## Versioning

Prefer URL versioning:
```
/api/v1/users
/api/v2/users
```

## Rate Limiting

Include headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

*Follow these patterns unless there's a specific reason to deviate.*
