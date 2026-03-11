# Benchmark: Java Simple POJO (Baseline)

## Category
java-unit

## Complexity
- Source lines: 20
- Mocks: 0
- Branches: 0
- Complexity score: 1

## Source Code

```java
public class User {
    private String email;
    private String name;
    private int age;

    public User(String email, String name, int age) {
        this.email = email;
        this.name = name;
        this.age = age;
    }

    public String getEmail() { return email; }
    public String getName() { return name; }
    public int getAge() { return age; }

    public boolean isAdult() { return age >= 18; }
}
```

## Prompt

```
Generate 3 JUnit 5 unit tests for this User class. Test the constructor, getters, and isAdult() method. Use Given-When-Then structure.

public class User {
    private String email;
    private String name;
    private int age;

    public User(String email, String name, int age) {
        this.email = email;
        this.name = name;
        this.age = age;
    }

    public String getEmail() { return email; }
    public String getName() { return name; }
    public int getAge() { return age; }

    public boolean isAdult() { return age >= 18; }
}
```

## Expected Output
- 3 test methods
- No mocking required
- Simple assertions (assertEquals, assertTrue/assertFalse)
