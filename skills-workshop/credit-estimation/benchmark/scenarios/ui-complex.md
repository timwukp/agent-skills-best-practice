# Benchmark: Selenium UI Multi-Step Form

## Category
ui

## Complexity
- Page elements: 8 (form, 5 inputs, checkbox, button)
- Steps: 7 (fill 5 fields, check box, submit)
- Waits: 3
- Validation: error messages
- Complexity score: 4

## Prompt

```
Generate 1 Selenium WebDriver test (JUnit 5) for a user registration form:
- URL: http://localhost:3000/register
- Form: data-testid="register-form"
- Fields:
  - First name: data-testid="firstname-input"
  - Last name: data-testid="lastname-input"
  - Email: data-testid="email-input"
  - Password: data-testid="password-input"
  - Confirm password: data-testid="confirm-password-input"
  - Terms checkbox: data-testid="terms-checkbox"
- Submit button: data-testid="register-button"
- Success: redirect to /welcome with data-testid="welcome-message"

Use explicit waits. ChromeDriver headless mode.
Test data: John, Doe, john@example.com, SecurePass123!, SecurePass123!
```

## Expected Output
- 1 test method with setUp/tearDown
- 7+ interactions with the page
- Explicit waits for form load and redirect
- Multiple data-testid selectors
