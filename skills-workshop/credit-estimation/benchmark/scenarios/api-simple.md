# Benchmark: REST API Simple GET

## Category
api

## Complexity
- Endpoint: GET /api/users
- Auth: none
- Response: JSON array
- Complexity score: 1

## Prompt

```
Generate 3 RestAssured API tests for a GET /api/users endpoint.
- 200 OK: returns a JSON array of users with fields: id, email, name
- 404: returns {"error": "No users found"} when collection is empty
- 500: returns {"error": "Internal server error"} for server failure

Base URL: http://localhost:8080
No authentication required.
```

## Expected Output
- 3 test methods using RestAssured given/when/then
- Status code assertions
- Response body assertions using Hamcrest matchers
