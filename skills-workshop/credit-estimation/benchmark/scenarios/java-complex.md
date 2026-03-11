# Benchmark: Java Service with Mocking

## Category
java-unit

## Complexity
- Source lines: 45
- Mocks: 2
- Branches: 4
- Complexity score: 5

## Source Code

```java
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    public OrderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
    }

    public Order placeOrder(Order order) {
        if (order == null) {
            throw new IllegalArgumentException("Order cannot be null");
        }
        if (order.getItems().isEmpty()) {
            throw new IllegalArgumentException("Order must have at least one item");
        }

        double total = order.getItems().stream()
            .mapToDouble(item -> item.getPrice() * item.getQuantity())
            .sum();

        if (total <= 0) {
            throw new IllegalArgumentException("Order total must be positive");
        }

        PaymentResult payment = paymentGateway.charge(order.getCustomerId(), total);
        if (!payment.isSuccess()) {
            throw new PaymentFailedException("Payment failed: " + payment.getError());
        }

        order.setTotal(total);
        order.setStatus("CONFIRMED");
        return orderRepository.save(order);
    }
}
```

## Prompt

```
Generate 3 JUnit 5 tests with Mockito for this OrderService.placeOrder() method. Cover: successful order, empty items validation, and payment failure. Use Given-When-Then structure.

public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    public OrderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
    }

    public Order placeOrder(Order order) {
        if (order == null) {
            throw new IllegalArgumentException("Order cannot be null");
        }
        if (order.getItems().isEmpty()) {
            throw new IllegalArgumentException("Order must have at least one item");
        }

        double total = order.getItems().stream()
            .mapToDouble(item -> item.getPrice() * item.getQuantity())
            .sum();

        if (total <= 0) {
            throw new IllegalArgumentException("Order total must be positive");
        }

        PaymentResult payment = paymentGateway.charge(order.getCustomerId(), total);
        if (!payment.isSuccess()) {
            throw new PaymentFailedException("Payment failed: " + payment.getError());
        }

        order.setTotal(total);
        order.setStatus("CONFIRMED");
        return orderRepository.save(order);
    }
}
```

## Expected Output
- 3 test methods with @Mock annotations
- Mockito when/verify patterns
- Exception assertions
