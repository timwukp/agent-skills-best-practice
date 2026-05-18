# Benchmark: TypeScript Simple Class

## Category
typescript-unit

## Complexity
- Source lines: 20
- Mocks: 0
- Branches: 2
- Complexity score: 1

## Prompt

```
Generate 3 Jest tests for this TypeScript class:

export class EmailValidator {
  validate(email: string): boolean {
    if (!email || email.trim().length === 0) {
      throw new Error('Email cannot be empty');
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

Test cases: valid email returns true, invalid email returns false, empty string throws error.
```

## Expected Output
- 3 test cases using Jest describe/it blocks
- expect().toBe() for boolean checks
- expect().toThrow() for error case
