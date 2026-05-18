# Benchmark: Python Simple Function

## Category
python-unit

## Complexity
- Source lines: 15
- Mocks: 0
- Branches: 1
- Complexity score: 1

## Prompt

```
Generate 3 pytest tests for this Python function:

def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price. Raises ValueError if inputs are negative."""
    if price < 0 or discount_percent < 0:
        raise ValueError("Price and discount must be non-negative")
    if discount_percent > 100:
        raise ValueError("Discount cannot exceed 100%")
    return price * (1 - discount_percent / 100)

Test cases: valid discount, negative price error, discount > 100% error.
```

## Expected Output
- 3 test functions using pytest
- pytest.raises for error cases
- Simple assertions with approx for floating point
