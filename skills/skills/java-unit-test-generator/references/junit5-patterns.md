# JUnit 5 Common Patterns

## Test Structure: Given-When-Then

```java
@Test
@DisplayName("Should create user when valid input provided")
void shouldCreateUser_whenValidInput() {
    // Given - setup test data
    User user = new User("john@example.com", "John Doe");
    when(userRepository.save(any(User.class))).thenReturn(user);
    
    // When - execute the method under test
    User result = userService.createUser(user);
    
    // Then - verify the outcome
    assertNotNull(result);
    assertEquals("john@example.com", result.getEmail());
    verify(userRepository, times(1)).save(user);
}
```

## Exception Testing

```java
@Test
void shouldThrowException_whenEmailIsNull() {
    User user = new User(null, "John Doe");
    
    assertThrows(IllegalArgumentException.class, () -> {
        userService.createUser(user);
    });
}
```

## Parameterized Tests

```java
@ParameterizedTest
@ValueSource(strings = {"", "  ", "invalid-email"})
void shouldRejectInvalidEmails(String email) {
    User user = new User(email, "John Doe");
    
    assertThrows(ValidationException.class, () -> {
        userService.createUser(user);
    });
}
```

## Mockito Patterns

### Basic Mocking
```java
@Mock
private UserRepository userRepository;

@InjectMocks
private UserService userService;

@BeforeEach
void setUp() {
    MockitoAnnotations.openMocks(this);
}
```

### Argument Captors
```java
@Test
void shouldSaveUserWithHashedPassword() {
    ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
    
    userService.createUser(new User("test@example.com", "password123"));
    
    verify(userRepository).save(userCaptor.capture());
    assertTrue(userCaptor.getValue().getPassword().startsWith("$2a$"));
}
```

## Test Lifecycle

```java
@BeforeAll
static void initAll() {
    // Runs once before all tests
}

@BeforeEach
void init() {
    // Runs before each test
}

@AfterEach
void tearDown() {
    // Runs after each test
}

@AfterAll
static void tearDownAll() {
    // Runs once after all tests
}
```

## Assertions

```java
// Basic assertions
assertEquals(expected, actual);
assertNotNull(object);
assertTrue(condition);
assertFalse(condition);

// Collection assertions
assertIterableEquals(expectedList, actualList);
assertArrayEquals(expectedArray, actualArray);

// Exception assertions
assertThrows(Exception.class, () -> method());
assertDoesNotThrow(() -> method());

// Timeout assertions
assertTimeout(Duration.ofSeconds(1), () -> method());
```
