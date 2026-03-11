package com.example.service;

import com.example.model.User;
import com.example.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Example test class for UserService demonstrating best practices.
 */
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    @DisplayName("Should create user successfully when valid input provided")
    void shouldCreateUserSuccessfully_whenValidInput() {
        // Given
        User user = new User("john@example.com", "John Doe");
        when(userRepository.save(any(User.class))).thenReturn(user);
        when(userRepository.findByEmail(user.getEmail())).thenReturn(Optional.empty());

        // When
        User result = userService.createUser(user);

        // Then
        assertNotNull(result);
        assertEquals("john@example.com", result.getEmail());
        assertEquals("John Doe", result.getName());
        verify(userRepository, times(1)).save(user);
    }

    @Test
    @DisplayName("Should throw exception when email is null")
    void shouldThrowException_whenEmailIsNull() {
        // Given
        User user = new User(null, "John Doe");

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            userService.createUser(user);
        });
        
        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    @DisplayName("Should throw exception when email already exists")
    void shouldThrowException_whenEmailAlreadyExists() {
        // Given
        User existingUser = new User("john@example.com", "Existing User");
        when(userRepository.findByEmail("john@example.com"))
            .thenReturn(Optional.of(existingUser));

        User newUser = new User("john@example.com", "John Doe");

        // When & Then
        assertThrows(DuplicateEmailException.class, () -> {
            userService.createUser(newUser);
        });
        
        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    @DisplayName("Should throw exception when name is empty")
    void shouldThrowException_whenNameIsEmpty() {
        // Given
        User user = new User("john@example.com", "");

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            userService.createUser(user);
        });
    }

    @Test
    @DisplayName("Should trim whitespace from email before saving")
    void shouldTrimWhitespace_whenEmailHasSpaces() {
        // Given
        User user = new User("  john@example.com  ", "John Doe");
        when(userRepository.save(any(User.class))).thenReturn(user);
        when(userRepository.findByEmail(anyString())).thenReturn(Optional.empty());

        // When
        User result = userService.createUser(user);

        // Then
        assertEquals("john@example.com", result.getEmail());
    }
}
