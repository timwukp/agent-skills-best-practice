package com.example.ui;

import org.junit.jupiter.api.*;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Example Selenium UI test for React login flow.
 * Demonstrates best practices with data-testid selectors and explicit waits.
 */
class LoginFlowTest {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeEach
    void setUp() {
        ChromeOptions options = new ChromeOptions();
        
        // Headless mode for CI/CD
        if (System.getProperty("headless", "false").equals("true")) {
            options.addArguments("--headless");
        }
        
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    @AfterEach
    void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    @DisplayName("Should login successfully with valid credentials")
    void shouldLoginSuccessfully_whenValidCredentials() {
        // Navigate to login page
        driver.get("http://localhost:3000/login");
        
        // Wait for login form to load
        wait.until(ExpectedConditions.presenceOfElementLocated(
            By.cssSelector("[data-testid='login-form']")
        ));
        
        // Fill username
        WebElement usernameField = driver.findElement(
            By.cssSelector("[data-testid='username-input']")
        );
        usernameField.sendKeys("testuser@example.com");
        
        // Fill password
        WebElement passwordField = driver.findElement(
            By.cssSelector("[data-testid='password-input']")
        );
        passwordField.sendKeys("password123");
        
        // Click login button
        WebElement loginButton = driver.findElement(
            By.cssSelector("[data-testid='login-button']")
        );
        loginButton.click();
        
        // Wait for redirect to dashboard
        wait.until(ExpectedConditions.urlContains("/dashboard"));
        
        // Verify successful login
        assertTrue(driver.getCurrentUrl().contains("/dashboard"));
        
        // Verify welcome message appears
        WebElement welcomeMessage = wait.until(
            ExpectedConditions.presenceOfElementLocated(
                By.cssSelector("[data-testid='welcome-message']")
            )
        );
        assertTrue(welcomeMessage.isDisplayed());
    }

    @Test
    @DisplayName("Should show error message with invalid credentials")
    void shouldShowError_whenInvalidCredentials() {
        driver.get("http://localhost:3000/login");
        
        wait.until(ExpectedConditions.presenceOfElementLocated(
            By.cssSelector("[data-testid='login-form']")
        ));
        
        // Fill with invalid credentials
        driver.findElement(By.cssSelector("[data-testid='username-input']"))
            .sendKeys("invalid@example.com");
        driver.findElement(By.cssSelector("[data-testid='password-input']"))
            .sendKeys("wrongpassword");
        
        // Submit
        driver.findElement(By.cssSelector("[data-testid='login-button']"))
            .click();
        
        // Wait for error message
        WebElement errorMessage = wait.until(
            ExpectedConditions.presenceOfElementLocated(
                By.cssSelector("[data-testid='error-message']")
            )
        );
        
        // Verify error is displayed
        assertTrue(errorMessage.isDisplayed());
        assertTrue(errorMessage.getText().contains("Invalid credentials"));
        
        // Verify still on login page
        assertTrue(driver.getCurrentUrl().contains("/login"));
    }

    @Test
    @DisplayName("Should disable login button when fields are empty")
    void shouldDisableLoginButton_whenFieldsEmpty() {
        driver.get("http://localhost:3000/login");
        
        wait.until(ExpectedConditions.presenceOfElementLocated(
            By.cssSelector("[data-testid='login-form']")
        ));
        
        // Get login button
        WebElement loginButton = driver.findElement(
            By.cssSelector("[data-testid='login-button']")
        );
        
        // Verify button is disabled when fields are empty
        assertFalse(loginButton.isEnabled());
        
        // Fill only username
        driver.findElement(By.cssSelector("[data-testid='username-input']"))
            .sendKeys("test@example.com");
        
        // Button should still be disabled
        assertFalse(loginButton.isEnabled());
        
        // Fill password
        driver.findElement(By.cssSelector("[data-testid='password-input']"))
            .sendKeys("password");
        
        // Now button should be enabled
        assertTrue(loginButton.isEnabled());
    }
}
