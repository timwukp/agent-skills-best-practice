# Benchmark: REST API POST with Validation

## Category
api

## Complexity
- Endpoint: POST /api/orders
- Auth: Bearer token
- Request body: nested JSON
- Complexity score: 4

## Prompt

```
Generate 3 RestAssured API tests for POST /api/orders endpoint.

Request body:
{
  "customerId": "cust-123",
  "items": [
    {"productId": "prod-1", "quantity": 2, "price": 29.99}
  ],
  "shippingAddress": {
    "street": "123 Main St",
    "city": "Seattle",
    "state": "WA",
    "zip": "98101"
  }
}

Test scenarios:
- 201 Created: valid order returns order with id, total, status="PENDING"
- 400 Bad Request: missing items array returns validation error
- 401 Unauthorized: no Bearer token returns auth error

Base URL: http://localhost:8080
Auth: Bearer token in Authorization header
```

## Expected Output
- 3 test methods with nested JSON bodies
- Auth header handling
- Nested response body assertions
