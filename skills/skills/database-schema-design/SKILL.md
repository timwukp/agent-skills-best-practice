---
name: database-schema-design
description: >
  Designs normalized database schemas with migration scripts, indexing strategies,
  and relationship handling. Supports SQL, Flyway, Liquibase, and Prisma.
  Triggers on: "design database", "create schema", "database migration", "design tables".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: data-engineering
---

# Database Schema Design

## Instructions

### Step 1: Gather Requirements

Ask:
1. What entities need to be stored? (e.g., users, orders, products)
2. What are the relationships? (one-to-one, one-to-many, many-to-many)
3. What queries will be most common? (affects indexing decisions)
4. Expected scale? (thousands vs millions of rows)
5. Database engine? (PostgreSQL, MySQL, SQLite)
6. Migration tool? (raw SQL, Flyway, Liquibase, Prisma, Alembic)

### Step 2: Design Normalized Schema

Apply normalization rules:

**First Normal Form (1NF):**
- Eliminate repeating groups
- Each column holds atomic values
- Each row is unique (has primary key)

**Second Normal Form (2NF):**
- Meet 1NF
- Remove partial dependencies on composite keys

**Third Normal Form (3NF):**
- Meet 2NF
- Remove transitive dependencies

**When to denormalize:**
- Read-heavy workloads with expensive joins
- Reporting tables (materialize aggregations)
- Caching frequently computed values with clear update triggers

Always start normalized, then denormalize with documented justification.

### Step 3: Define Tables

Use this format for each table:

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    shipping_address_id UUID REFERENCES addresses(id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE orders IS 'Customer purchase orders';
COMMENT ON COLUMN orders.total_cents IS 'Order total in smallest currency unit';
```

**Conventions:**
- Use UUID for primary keys (or BIGSERIAL if performance-critical)
- Store money as integers (cents) to avoid floating point issues
- Use TIMESTAMPTZ (not TIMESTAMP) for all time columns
- Add CHECK constraints for enum-like values
- Include created_at and updated_at on every table
- Use ON DELETE CASCADE or SET NULL explicitly

### Step 4: Handle Relationships

**One-to-Many (e.g., user has many orders):**
```sql
-- FK on the "many" side
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
    FOREIGN KEY (user_id) REFERENCES users(id);
```

**Many-to-Many (e.g., orders have many products):**
```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price_cents BIGINT NOT NULL,
    UNIQUE (order_id, product_id)
);
```

**One-to-One (e.g., user has one profile):**
```sql
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url TEXT
);
```

### Step 5: Indexing Strategy

Create indexes based on query patterns:

```sql
-- Columns used in WHERE clauses
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status) WHERE status != 'cancelled';

-- Columns used in ORDER BY
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Composite index for common filter + sort
CREATE INDEX idx_orders_user_status_date
    ON orders(user_id, status, created_at DESC);

-- Full-text search
CREATE INDEX idx_products_search
    ON products USING GIN(to_tsvector('english', name || ' ' || description));

-- Unique constraints that are also indexes
CREATE UNIQUE INDEX idx_users_email ON users(LOWER(email));
```

**Index rules:**
- Index foreign keys (PostgreSQL does not do this automatically)
- Use partial indexes for filtered queries
- Composite indexes: put equality columns first, range columns last
- Do not index columns with low cardinality unless combined with others
- Monitor with `pg_stat_user_indexes` to find unused indexes

### Step 6: Generate Migration Script

**Raw SQL (Flyway-compatible naming: V001__create_users.sql):**
```sql
-- V001__create_users.sql
BEGIN;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_users_email ON users(LOWER(email));

COMMIT;
```

**Prisma schema:**
```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  orders    Order[]
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("users")
}
```

**Alembic (Python):**
```python
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', [sa.text('LOWER(email)')], unique=True)
```

### Step 7: Add Trigger for updated_at

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

Apply this trigger to every table with an `updated_at` column.

## Example

User says: "Design a database for a blog with users, posts, and comments"

Response:
- users table (id, email, display_name, created_at)
- posts table (id, author_id FK, title, slug, body, status, published_at)
- comments table (id, post_id FK, author_id FK, parent_id FK for threading, body)
- Indexes on foreign keys and slug
- Migration script in requested format

## Guidelines

- Always use UUID or BIGSERIAL for primary keys, never application-meaningful values
- Store monetary values as integers in the smallest unit (cents, pence)
- Use TIMESTAMPTZ for all datetime columns
- Every table gets id, created_at, updated_at as minimum columns
- Index all foreign key columns
- Wrap migrations in transactions
- Provide rollback (DOWN) migration alongside the upgrade
- Recommend PostgreSQL as the default unless there is a reason for another engine
