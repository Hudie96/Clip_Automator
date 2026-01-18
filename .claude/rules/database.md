# Database Design Standards

## Schema Design

### Naming Conventions
- Tables: `snake_case`, plural (`users`, `order_items`)
- Columns: `snake_case` (`created_at`, `user_id`)
- Primary keys: `id` (UUID or auto-increment)
- Foreign keys: `{table}_id` (`user_id`, `order_id`)
- Indexes: `idx_{table}_{column}` (`idx_users_email`)
- Constraints: `{table}_{type}_{column}` (`users_unique_email`)

### Required Columns
Every table should have:
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

### Soft Deletes (Optional)
```sql
deleted_at  TIMESTAMP WITH TIME ZONE NULL
```

## Indexing

### When to Index
✅ Primary keys (automatic)
✅ Foreign keys
✅ Columns in WHERE clauses
✅ Columns in ORDER BY
✅ Columns in JOIN conditions

### When NOT to Index
❌ Low-cardinality columns (boolean, enum with few values)
❌ Frequently updated columns
❌ Small tables (<1000 rows)

### Composite Indexes
Order matters! Put most selective column first:
```sql
CREATE INDEX idx_orders_user_status 
ON orders(user_id, status);
-- Helps: WHERE user_id = ? AND status = ?
-- Helps: WHERE user_id = ?
-- Doesn't help: WHERE status = ?
```

## Migrations

### Principles
1. Migrations are immutable once deployed
2. Always provide rollback (`down`)
3. Keep migrations small and focused
4. Test migrations on production-like data

### Safe Migration Practices
```sql
-- Adding column (safe)
ALTER TABLE users ADD COLUMN middle_name VARCHAR(100);

-- Adding NOT NULL column (use default first)
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
UPDATE users SET status = 'active' WHERE status IS NULL;
ALTER TABLE users ALTER COLUMN status SET NOT NULL;

-- Removing column (two-step)
-- Step 1: Stop writing to column, deploy
-- Step 2: Remove column, deploy
```

### Dangerous Operations
⚠️ These can lock tables or cause downtime:
- `ALTER TABLE ... ADD COLUMN ... NOT NULL` without default
- `CREATE INDEX` on large tables (use `CONCURRENTLY`)
- `ALTER TABLE ... ALTER COLUMN TYPE`
- Bulk `UPDATE` or `DELETE`

## Query Patterns

### N+1 Problem
```typescript
// Bad: N+1 queries
const users = await db.users.findMany();
for (const user of users) {
  user.posts = await db.posts.findMany({ where: { userId: user.id } });
}

// Good: eager loading
const users = await db.users.findMany({
  include: { posts: true }
});
```

### Pagination
```typescript
// Offset pagination (simple but slow at scale)
const users = await db.users.findMany({
  skip: (page - 1) * limit,
  take: limit
});

// Cursor pagination (better for large datasets)
const users = await db.users.findMany({
  take: limit,
  cursor: { id: lastId },
  skip: 1 // Skip the cursor itself
});
```

### Transactions
```typescript
await db.$transaction(async (tx) => {
  const user = await tx.users.create({ data: userData });
  await tx.accounts.create({ data: { userId: user.id } });
  // Both succeed or both fail
});
```

## Security

### SQL Injection Prevention
Always use parameterized queries:
```typescript
// Bad
db.query(`SELECT * FROM users WHERE email = '${email}'`);

// Good
db.query('SELECT * FROM users WHERE email = $1', [email]);

// Good (ORM)
db.users.findUnique({ where: { email } });
```

### Sensitive Data
- Hash passwords (bcrypt, argon2)
- Encrypt PII at rest
- Don't log sensitive queries
- Use separate read-only credentials for analytics

---

*Design for scale, optimize for reality.*
