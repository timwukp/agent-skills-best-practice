---
name: selenium-ui-test-generator
description: >
  Generates Selenium WebDriver tests for React/Angular front-ends with STRICT loop prevention.
  Triggers on: "test UI", "generate Selenium tests", "test React app", "create E2E tests", "test front-end".
  WARNING: UI tests cost 3x more than unit tests -- generate selectively.
license: MIT
metadata:
  author: Kiro Solutions Team
  version: 1.1.0
  frameworks: Selenium WebDriver, JUnit 5
  credit-estimate: 30-50 per test
---

# Selenium UI Test Generator

**Cost warning:** UI tests cost 30-50 credits each (vs. 10-15 for unit tests). Always inform the user of this before generating.

## Instructions

### Step 1: Flow Selection

Ask the user to pick **2-3 critical flows maximum** (e.g., login, form submission, checkout). Provide cost comparison so they can make an informed choice.

### Step 2: Get Selectors Upfront

**This is critical for avoiding wasted iterations.** Ask the user to provide:
1. `data-testid` attributes (preferred)
2. Or element IDs/classes from browser dev tools

Without real selectors, tests will likely fail and waste credits. If the user cannot provide selectors, warn them of the higher failure risk before proceeding.

See `references/react-testid-guide.md` for the recommended `data-testid` pattern.
Load selectors from `assets/selectors-config.json` when available.

### Step 3: Generate ONE Test at a Time

Unlike unit/API skills, generate only **1 UI test per iteration** due to the high cost.

Use explicit waits and `data-testid` selectors:
```java
@Test
void testUserLogin() {
    driver.get("http://localhost:3000/login");

    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    wait.until(ExpectedConditions.presenceOfElementLocated(
        By.cssSelector("[data-testid='login-form']")
    ));

    driver.findElement(By.cssSelector("[data-testid='username-input']"))
        .sendKeys("testuser@example.com");
    driver.findElement(By.cssSelector("[data-testid='password-input']"))
        .sendKeys("password123");
    driver.findElement(By.cssSelector("[data-testid='login-button']"))
        .click();

    wait.until(ExpectedConditions.urlContains("/dashboard"));
    assertTrue(driver.getCurrentUrl().contains("/dashboard"));
}
```

**STOP.** Ask the user to run the test before continuing.

### Step 4: Validation

```bash
python scripts/validate_ui_tests.py <TestClassName>
```

Add `--headed` to see the browser during debugging.

### Step 5: Fix or Skip (STRICT -- Max 2 Attempts)

If test fails:
- **Attempt 1:** Add explicit waits, use more specific selectors, handle React loading states
- **Attempt 2:** Try different selector strategy (XPath vs CSS), longer waits, check for overlays/modals
- **After 2 failures:** STOP. UI selector issues rarely resolve with more guessing.

Report credits used and credits saved by stopping.

### Step 6: Page Object (Optional)

If the user has multiple tests for the same page, offer to create a Page Object class. This costs ~20 credits upfront but saves ~10 credits per additional test on that page.

### Step 7: Summary Report

```
Flows Tested: N
Tests Generated: N
Tests Skipped: N (with reasons)
Credits Used: N
Credits Saved by Skipping: N
```

## Measuring Credit Cost for Your UI Flows

Credit costs vary by Kiro account, model, and flow complexity. UI tests are the most
expensive category because they generate more code (setup, waits, selectors, teardown)
and fail more often (leading to retries that cost additional credits).

### 1. Establish your baseline (one-time)

Run the built-in benchmark with a simple login flow:

```bash
python track_credits.py benchmark ui-simple
```

This measures the cheapest possible UI test on your account (e.g., 0.21 credits/test).

### 2. Why UI tests cost more than unit or API tests

- The AI generates more code: driver setup, Chrome options, explicit waits, selector
  lookups, teardown
- The AI needs more context: your selector config, page structure, wait strategies
- UI tests fail more often, and each retry costs additional credits

### 3. Estimate before running on your flow

More complex flows cost more:

| What makes UI tests cost more | How it's scored |
|------------------------------|----------------|
| More page interactions (clicks, fills) | +1 for every 3 steps |
| Dynamic elements (React state, conditional rendering) | +2 for each dynamic element |
| Multi-page navigation | +2 for each page transition |
| More waits needed | +1 for every 3 waits |

```bash
python track_credits.py estimate \
  --type ui \
  --source-lines 50 \
  --branches 2 \
  --dynamic-selectors 1 \
  --tests 1
```

### 4. Measure actual cost after running

```bash
# Note credit balance before and after, then record:
python track_credits.py add "LoginFlow-1test" <before> <after> "1 Selenium test, 4 selectors"
```

Your measurements improve future estimates automatically.
See `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` for the full guide.

## References

- `references/examples/LoginFlowTest.java` - Complete Selenium example
- `references/react-testid-guide.md` - Guide for adding data-testid to React components
- `assets/selectors-config.json` - Example selector configuration
- `../../../skills-workshop/credit-estimation/CREDIT-ESTIMATION-GUIDE.md` - Credit measurement methodology
- [Selenium WebDriver Docs](https://www.selenium.dev/documentation/)
- [data-testid Pattern](https://kentcdodds.com/blog/making-your-ui-tests-resilient-to-change)
