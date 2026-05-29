---
name: api-design
description: >
  Generates RESTful API designs with OpenAPI specs, proper resource naming, HTTP method usage,
  status codes, pagination, filtering, error responses, and versioning strategies.
  Triggers on: "design API", "create API spec", "OpenAPI", "REST endpoint design".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: api-development
---

# API Design

## Instructions

### Step 1: Gather Requirements

Ask:
1. What resources does this API manage? (e.g., users, orders, products)
2. What operations are needed? (CRUD, search, bulk operations, async jobs)
3. Who consumes it? (internal services, public clients, mobile apps)
4. Auth model? (API key, OAuth2, JWT)
5. Output format preference? (OpenAPI 3.0 YAML, endpoint list, or both)

### Step 2: Resource Naming

Apply these naming conventions:

| Rule | Good | Bad |
|------|------|-----|
| Plural nouns | `/users` | `/user`, `/getUsers` |
| Nested resources | `/users/{id}/orders` | `/getUserOrders` |
| Lowercase with hyphens | `/order-items` | `/orderItems`, `/order_items` |
| No verbs in URLs | `/users/{id}/activate` (POST) | `/activateUser` |
| Max 3 levels deep | `/users/{id}/orders` | `/users/{id}/orders/{id}/items/{id}/reviews` |

For deeply nested resources, promote to top-level with query filters:
```
GET /reviews?order_id=123&user_id=456
```

### Step 3: HTTP Methods and Status Codes

Map operations to methods:

| Operation | Method | Success Code | Response Body |
|-----------|--------|-------------|---------------|
| List/Search | GET | 200 | Collection |
| Get single | GET | 200 | Resource |
| Create | POST | 201 | Created resource + Location header |
| Full update | PUT | 200 | Updated resource |
| Partial update | PATCH | 200 | Updated resource |
| Delete | DELETE | 204 | Empty |
| Async operation | POST | 202 | Job status + Location header |

**Error codes to use consistently:**
- 400 - Malformed request (bad JSON, missing required field)
- 401 - Not authenticated
- 403 - Authenticated but not authorized
- 404 - Resource not found
- 409 - Conflict (duplicate, version mismatch)
- 422 - Valid JSON but failed business validation
- 429 - Rate limited
- 500 - Server error (never expose internals)

### Step 4: Pagination, Filtering, and Sorting

**Pagination (cursor-based preferred for large datasets):**
```
GET /orders?cursor=eyJpZCI6MTAwfQ&limit=25

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTI1fQ",
    "has_more": true
  }
}
```

**Offset pagination (simpler, fine for small datasets):**
```
GET /orders?page=2&per_page=25

Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 25,
    "total": 142,
    "total_pages": 6
  }
}
```

**Filtering and sorting:**
```
GET /orders?status=pending&created_after=2024-01-01&sort=-created_at,+total
```

- Use query parameters for filtering
- Prefix sort fields with `-` for descending, `+` for ascending
- Document all available filter fields

### Step 5: Error Response Format

Use a consistent error envelope:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request body contains invalid fields",
    "details": [
      {
        "field": "email",
        "issue": "must be a valid email address",
        "value": "not-an-email"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://api.example.com/docs/errors#VALIDATION_FAILED"
  }
}
```

**Rules:**
- Machine-readable `code` (UPPER_SNAKE_CASE)
- Human-readable `message`
- Field-level `details` for validation errors
- Include `request_id` for debugging
- Never expose stack traces, SQL, or internal paths

### Step 6: Generate OpenAPI Spec

Produce an OpenAPI 3.0 specification:

```yaml
openapi: 3.0.3
info:
  title: [Service Name] API
  version: 1.0.0
  description: [Brief description]
paths:
  /resources:
    get:
      summary: List resources
      operationId: listResources
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 25
            maximum: 100
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
components:
  schemas:
    Resource:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
```

### Step 7: Versioning Strategy

Recommend URL-path versioning for most cases:
```
/v1/users
/v2/users
```

**When to create a new version:**
- Removing a field from responses
- Changing a field type
- Removing an endpoint
- Changing authentication mechanism

**When NOT to version (additive changes):**
- Adding new optional fields
- Adding new endpoints
- Adding new query parameters

## Example

User says: "Design an API for a bookstore"

Response includes:
- Resource list: books, authors, orders, customers
- Endpoints: `GET /v1/books`, `POST /v1/orders`, etc.
- OpenAPI snippet for the books resource
- Error response format
- Pagination on list endpoints

## Guidelines

- Always use plural nouns for resource names
- Prefer cursor pagination for datasets that change frequently
- Use 422 for business logic validation, 400 for malformed requests
- Include rate limiting headers in responses (X-RateLimit-Remaining, X-RateLimit-Reset)
- Design for the consumer, not the database schema
- Every endpoint must have a defined error response
- Keep the OpenAPI spec as the source of truth, generate docs from it
