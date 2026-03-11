# Credit Measurement Test Plan

## Objective
Measure actual credit consumption for each skill type to validate the estimates in README.md

## Test Scenarios

### 1. Java Unit Test Generator (Claimed: 10-15 credits/test)

**Test Case 1: Simple POJO**
```java
public class User {
    private String email;
    private String name;
    
    public User(String email, String name) {
        this.email = email;
        this.name = name;
    }
    
    public String getEmail() { return email; }
    public String getName() { return name; }
}
```
**Prompt:** "Generate 3 unit tests for the User class constructor and getters"

**Test Case 2: Service with Mocking**
```java
public class UserService {
    private UserRepository repository;
    
    public User createUser(User user) {
        if (user.getEmail() == null) {
            throw new IllegalArgumentException("Email required");
        }
        return repository.save(user);
    }
}
```
**Prompt:** "Generate 3 unit tests for UserService.createUser() with Mockito"

---

### 2. REST API Test Generator (Claimed: 15-20 credits/test)

**Test Case 1: Simple GET**
**Prompt:** "Generate 3 API tests for GET /api/users endpoint that returns a list of users"

**Test Case 2: POST with Validation**
**Prompt:** "Generate 3 API tests for POST /api/users endpoint with request body validation (email required, name required)"

---

### 3. Selenium UI Test Generator (Claimed: 30-50 credits/test)

**Test Case 1: Simple Login**
**Prompt:** "Generate 1 Selenium test for login flow with username/password fields and submit button"

**Test Case 2: Form Submission**
**Prompt:** "Generate 1 Selenium test for user registration form with 5 fields (name, email, password, confirm password, terms checkbox)"

---

## Measurement Protocol

### Before Each Test:
1. Note starting credit balance
2. Clear conversation context (start fresh chat)
3. Copy exact prompt from test case

### During Test:
4. Paste prompt into Kiro CLI
5. Let AI complete the generation
6. Do NOT ask for fixes or iterations (measure first-pass only)

### After Each Test:
7. Note ending credit balance
8. Calculate: `credits_used = start_balance - end_balance`
9. Record in results table below

---

## Results Template

| Test Case | Start Credits | End Credits | Used | Claimed Range | Variance |
|-----------|---------------|-------------|------|---------------|----------|
| Java - Simple POJO (3 tests) | | | | 30-45 | |
| Java - Service w/ Mock (3 tests) | | | | 30-45 | |
| API - Simple GET (3 tests) | | | | 45-60 | |
| API - POST Validation (3 tests) | | | | 45-60 | |
| UI - Simple Login (1 test) | | | | 30-50 | |
| UI - Form Submission (1 test) | | | | 30-50 | |

---

## Analysis

After completing all tests:

1. **Per-test averages:**
   - Java Unit: `(test1 + test2) / 6 tests` vs claimed 10-15
   - REST API: `(test1 + test2) / 6 tests` vs claimed 15-20
   - Selenium UI: `(test1 + test2) / 2 tests` vs claimed 30-50

2. **Variance analysis:**
   - If actual > claimed: Update README with realistic numbers
   - If actual < claimed: Great! But verify with more samples
   - If variance > 50%: Add disclaimer about complexity factors

3. **Update documentation:**
   - Add "Based on testing with [model name] on [date]"
   - Include sample size and variance range
   - Add factors that increase cost (complex mocking, nested objects, etc.)
