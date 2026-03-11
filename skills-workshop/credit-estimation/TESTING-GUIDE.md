# Quick Start: Credit Testing with Kiro CLI

## Setup (One-time)

```bash
cd Skills-examples-javatest-UItest
python track_credits.py init
```

Then edit `credit-test-results.json` and update the `"model"` field with your current Kiro model (e.g., "claude-3-5-sonnet-20241022").

---

## Testing Workflow

### For Each Test:

1. **Check your current credits:**
   ```bash
   # In Kiro CLI, type:
   /model
   ```
   Note the credit balance (e.g., 1000)

2. **Start a fresh conversation:**
   ```bash
   # Exit current chat and start new one
   /quit
   kiro-cli chat
   ```

3. **Run the test prompt** (copy from test-credit-measurement.md)

4. **Check credits again:**
   ```bash
   /model
   ```
   Note the new balance (e.g., 985)

5. **Record the result:**
   ```bash
   python track_credits.py add "Java-SimplePOJO" 1000 985 "3 tests for User class"
   ```

---

## Example Test Sequence

### Test 1: Java Unit Test (Simple)

```bash
# 1. Check credits
/model  # Note: 1000 credits

# 2. In Kiro CLI, paste this prompt:
Generate 3 unit tests for this Java class:

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

# 3. Wait for completion, then check credits
/model  # Note: 985 credits

# 4. Record result
python track_credits.py add "Java-SimplePOJO-3tests" 1000 985
```

### Test 2: Java Unit Test (With Mocking)

```bash
# Start fresh chat
/quit
kiro-cli chat

# Check credits
/model  # Note: 985 credits

# Paste prompt:
Generate 3 unit tests with Mockito for this service:

public class UserService {
    private UserRepository repository;
    
    public User createUser(User user) {
        if (user.getEmail() == null) {
            throw new IllegalArgumentException("Email required");
        }
        return repository.save(user);
    }
}

# Check credits after
/model  # Note: 965 credits

# Record
python track_credits.py add "Java-ServiceMocking-3tests" 985 965
```

### Test 3: REST API Test

```bash
/quit
kiro-cli chat
/model  # Note: 965 credits

# Prompt:
Generate 3 RestAssured API tests for GET /api/users endpoint that returns:
- 200 OK with user list
- 404 when no users found
- 401 when unauthorized

/model  # Note: 940 credits
python track_credits.py add "API-SimpleGET-3tests" 965 940
```

### Test 4: Selenium UI Test

```bash
/quit
kiro-cli chat
/model  # Note: 940 credits

# Prompt:
Generate 1 Selenium test for login flow with:
- Username input (data-testid="username")
- Password input (data-testid="password")
- Submit button (data-testid="login-btn")
- Verify redirect to /dashboard

/model  # Note: 895 credits
python track_credits.py add "UI-SimpleLogin-1test" 940 895
```

---

## View Results

```bash
# Show summary in terminal
python track_credits.py summary

# Export to markdown
python track_credits.py export
# Creates: credit-test-results.md
```

---

## Recommended Test Order

Run tests in this order to maximize data collection with limited credits:

1. Java - Simple POJO (cheapest, baseline)
2. Java - Service with Mocking (measure complexity impact)
3. API - Simple GET (compare to Java)
4. API - POST with Validation (measure API complexity)
5. UI - Simple Login (most expensive, do last)
6. UI - Form Submission (if credits remain)

**Minimum viable test:** Run tests 1, 3, and 5 (one of each type) = ~60-80 credits total
