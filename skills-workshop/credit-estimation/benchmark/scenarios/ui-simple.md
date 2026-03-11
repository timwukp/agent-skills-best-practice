# Benchmark: Selenium UI Login Flow

## Category
ui

## Complexity
- Page elements: 4 (form, 2 inputs, button)
- Steps: 3 (fill username, fill password, click login)
- Waits: 2
- Complexity score: 1

## Prompt

```
Generate 1 Selenium WebDriver test (JUnit 5) for a login flow:
- URL: http://localhost:3000/login
- Username input: data-testid="username-input"
- Password input: data-testid="password-input"
- Login button: data-testid="login-button"
- After login, verify URL contains "/dashboard"

Use explicit waits (WebDriverWait, 10 seconds).
Use ChromeDriver with headless option.
Valid credentials: testuser@example.com / password123
```

## Expected Output
- 1 test method with setUp/tearDown
- ChromeOptions with headless
- WebDriverWait with ExpectedConditions
- CSS selectors using data-testid
