---
name: java-unit-test-generator
description: >
  Generates JUnit unit tests for Java classes with loop prevention and incremental generation.
  Triggers on: "generate unit tests", "create JUnit tests", "test Java class", "add test coverage".
license: MIT
metadata:
  author: Kiro Solutions Team
  version: 1.1.0
  target-framework: JUnit 5
  credit-estimate: 10-15 per test
---

# Java Unit Test Generator

## Instructions

### Step 1: Scope Definition

Before generating tests, ask:
1. Which class/method?
2. Coverage goal? (Basic = happy path | Standard = + errors | Comprehensive = + edge cases)
3. Framework? (JUnit 4, JUnit 5, TestNG)
4. Mocking? (Mockito, EasyMock, none)

Provide an upfront estimate: **10-15 credits per method**.

### Step 2: Generate 3 Tests Per Batch

For each method, generate exactly 3 tests:
1. Happy path
2. Error handling
3. Edge case

Use this structure:
```java
@Test
@DisplayName("Should [expected behavior] when [condition]")
void test[MethodName][Scenario]() {
    // Given - setup
    // When - execute
    // Then - verify
}
```

**STOP after each batch.** Ask the user to run and confirm before continuing.

### Step 3: Validation Gate

Do NOT generate more tests until the user confirms the current batch works.

Validation command:
```bash
python scripts/validate_tests.py <TestClassName>
```

### Step 4: Fix or Skip (Max 2 Attempts)

If tests fail:
- **Attempt 1:** Fix compilation errors (imports, syntax)
- **Attempt 2:** Fix logic errors (assertions, test data)
- **After 2 failures:** Skip the test, document the issue, and move on

When skipping, say:
> "This test failed twice. Skipping to preserve credits. Issue: [describe]. Options: (1) skip, (2) provide more context, (3) simplify scope."

Never attempt the same fix more than twice. Mark flaky tests `@Disabled`.

### Step 5: Iterate or Finish

After a passing batch, offer:
- 3 more tests for the same method
- Move to next method
- Stop and produce summary

### Step 6: Summary Report

```
Methods Tested: N
Total Tests: N
Skipped: N (with reasons)
Coverage: happy path / error / edge case breakdown
```

## Measuring Credit Cost for Your Code

Credit costs vary by Kiro account, model, and code complexity. To get accurate numbers
for your environment, follow these steps.

### 1. Establish your baseline (one-time)

Run the built-in benchmark with a simple sample class:

```bash
python track_credits.py benchmark java-simple
```

This measures the cheapest possible unit test on your account (e.g., 0.063 credits/test).

### 2. Estimate before running on your code

Your real classes are more complex. The tool scores complexity based on:

| What makes tests cost more | How it's scored |
|---------------------------|----------------|
| More lines of code | +1 for every 50 lines |
| More mock dependencies | +1 for each mock |
| More branching (if/else/switch) | +1 for every 3 branches |
| More framework annotations | +1 for every 3 annotations |

```bash
python track_credits.py estimate \
  --type java-unit \
  --source-lines 150 \
  --mocks 3 \
  --branches 6 \
  --annotations 4 \
  --tests 3
```

### 3. Measure actual cost after running

```bash
# Note credit balance before and after, then record:
python track_credits.py add "MyService-3tests" <before> <after> "3 JUnit5 tests, Mockito"
```

Your measurements improve future estimates automatically.
See `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` for the full guide.

## References

- `references/junit5-patterns.md` - Common JUnit 5 patterns
- `references/examples/UserServiceTest.java` - Complete example
- `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` - Credit measurement methodology
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/)
