---
name: rest-api-test-generator
description: >
  Generates REST API tests using RestAssured or MockMvc with loop prevention and incremental validation.
  Triggers on: "test API endpoints", "generate API tests", "test REST API", "create integration tests".
license: MIT
metadata:
  author: Kiro Solutions Team
  version: 1.1.0
  frameworks: RestAssured, Spring MockMvc
  credit-estimate: 15-20 per test
---

# REST API Test Generator

## Instructions

### Step 1: API Discovery

Ask the user:
1. Which endpoint? (e.g., `POST /api/users`)
2. Framework? (RestAssured, MockMvc)
3. Authentication? (Bearer token, Basic auth, none)
4. Test environment? (Mock server, local, staging)
5. Request body example and expected response codes

Provide an upfront estimate: **15-20 credits per test scenario**.

### Step 2: Generate 3 Scenarios Per Batch

Generate exactly 3 test scenarios:
1. **Success case** (e.g., 201 Created)
2. **Validation error** (e.g., 400 Bad Request)
3. **Business logic error** (e.g., 409 Conflict, 404 Not Found)

Use RestAssured template:
```java
@Test
void shouldCreateUser_whenValidRequest() {
    given()
        .contentType(ContentType.JSON)
        .body(validUserRequest)
    .when()
        .post("/api/users")
    .then()
        .statusCode(201)
        .body("id", notNullValue())
        .body("email", equalTo("test@example.com"));
}
```

**STOP after 3 tests.** Ask the user to run and confirm responses match.

### Step 3: Validation Gate

Validation command:
```bash
python scripts/validate_api_tests.py <TestClassName> --base-url http://localhost:8080
```

Do NOT generate more tests until the user confirms the current batch passes.

### Step 4: Fix or Skip (Max 2 Attempts)

If tests fail:
- **Attempt 1:** Check request/response format, Content-Type, auth token
- **Attempt 2:** Adjust assertions (nested paths, flexible matchers like `hasKey`, `anyOf`)
- **After 2 failures:** Skip and document expected vs. actual behavior

This usually indicates an API contract mismatch or environment issue -- not something more iterations will fix.

### Step 5: Iterate or Finish

After a passing batch, offer:
- Auth tests (401, 403)
- Additional validation scenarios
- Other endpoints
- Stop and produce summary

### Step 6: Summary Report

```
Endpoint: POST /api/users
Tests Generated: N
Status Codes Covered: 201, 400, 401, 409
Skipped: N (with reasons)
```

## Measuring Credit Cost for Your Endpoints

Credit costs vary by Kiro account, model, and endpoint complexity. To get accurate
numbers for your environment, follow these steps.

### 1. Establish your baseline (one-time)

Run the built-in benchmark with a simple GET endpoint:

```bash
python track_credits.py benchmark api-simple
```

This measures the cheapest possible API test on your account (e.g., 0.077 credits/test).

### 2. Estimate before running on your endpoint

Real API tests get more expensive with nested JSON, auth, and more assertions:

| What makes API tests cost more | How it's scored |
|-------------------------------|----------------|
| Deeper request/response JSON | +1 for each nesting level |
| More response assertions | +1 for every 3 assertions |
| Authentication setup | +1 for Bearer, +2 for OAuth flows |
| More status codes to test | +1 for every 3 codes |

```bash
python track_credits.py estimate \
  --type api \
  --nesting-levels 2 \
  --branches 4 \
  --annotations 3 \
  --tests 3
```

### 3. Measure actual cost after running

```bash
# Note credit balance before and after, then record:
python track_credits.py add "UsersAPI-POST-3tests" <before> <after> "3 RestAssured tests, auth"
```

Your measurements improve future estimates automatically.
See `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` for the full guide.

## References

- `references/examples/UserApiTest.java` - Complete RestAssured example
- `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` - Credit measurement methodology
- [RestAssured Documentation](https://rest-assured.io/)
- [Spring MockMvc Guide](https://spring.io/guides/gs/testing-web/)
