# React Component Test ID Guide

## Best Practice: Use data-testid Attributes

Add `data-testid` to all interactive elements in your React components:

```jsx
// Login.jsx
export function Login() {
  return (
    <form data-testid="login-form">
      <input
        type="email"
        data-testid="username-input"
        placeholder="Email"
      />
      <input
        type="password"
        data-testid="password-input"
        placeholder="Password"
      />
      <button
        type="submit"
        data-testid="login-button"
      >
        Login
      </button>
      <div data-testid="error-message" className="error">
        {errorMessage}
      </div>
    </form>
  );
}
```

## Naming Convention

Use descriptive, hierarchical names:

```
[component]-[element]-[type]

Examples:
- login-form
- username-input
- password-input
- submit-button
- error-message
- success-banner
```

## Common Patterns

### Forms
```jsx
<form data-testid="user-form">
  <input data-testid="name-input" />
  <input data-testid="email-input" />
  <button data-testid="submit-button">Submit</button>
</form>
```

### Lists
```jsx
<ul data-testid="user-list">
  {users.map(user => (
    <li key={user.id} data-testid={`user-item-${user.id}`}>
      {user.name}
    </li>
  ))}
</ul>
```

### Modals
```jsx
<div data-testid="confirmation-modal">
  <h2 data-testid="modal-title">Confirm Action</h2>
  <button data-testid="confirm-button">Confirm</button>
  <button data-testid="cancel-button">Cancel</button>
</div>
```

### Loading States
```jsx
{isLoading ? (
  <div data-testid="loading-spinner">Loading...</div>
) : (
  <div data-testid="content">{content}</div>
)}
```

## Why data-testid?

✅ **Stable** - Doesn't change with styling
✅ **Explicit** - Clear intent for testing
✅ **Isolated** - Doesn't affect production code
✅ **Searchable** - Easy to find in codebase

❌ **Avoid:**
- Class names (change with styling)
- IDs (may conflict)
- Text content (changes with i18n)
- Complex XPath (brittle)
