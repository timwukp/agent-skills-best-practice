package com.example.api;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

/**
 * Example REST API test using RestAssured.
 * Tests the /api/users endpoint.
 */
class UserApiTest {

    @BeforeAll
    static void setup() {
        RestAssured.baseURI = "http://localhost:8080";
        RestAssured.basePath = "/api";
    }

    @Test
    @DisplayName("Should create user and return 201 when valid request")
    void shouldCreateUser_whenValidRequest() {
        String requestBody = """
            {
                "email": "john@example.com",
                "name": "John Doe",
                "age": 30
            }
            """;

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post("/users")
        .then()
            .statusCode(201)
            .body("id", notNullValue())
            .body("email", equalTo("john@example.com"))
            .body("name", equalTo("John Doe"))
            .header("Location", matchesPattern("/api/users/\\d+"));
    }

    @Test
    @DisplayName("Should return 400 when email is missing")
    void shouldReturn400_whenEmailIsMissing() {
        String requestBody = """
            {
                "name": "John Doe",
                "age": 30
            }
            """;

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post("/users")
        .then()
            .statusCode(400)
            .body("error", equalTo("Validation failed"))
            .body("details", hasItem(containsString("email")));
    }

    @Test
    @DisplayName("Should return 409 when email already exists")
    void shouldReturn409_whenEmailAlreadyExists() {
        String requestBody = """
            {
                "email": "existing@example.com",
                "name": "John Doe",
                "age": 30
            }
            """;

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post("/users")
        .then()
            .statusCode(409)
            .body("error", equalTo("Email already exists"));
    }

    @Test
    @DisplayName("Should return 401 when no authentication token")
    void shouldReturn401_whenNoAuthToken() {
        String requestBody = """
            {
                "email": "john@example.com",
                "name": "John Doe"
            }
            """;

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
            // No Authorization header
        .when()
            .post("/users")
        .then()
            .statusCode(401)
            .body("error", equalTo("Unauthorized"));
    }

    @Test
    @DisplayName("Should get user by ID and return 200")
    void shouldGetUser_whenValidId() {
        given()
            .header("Authorization", "Bearer valid-token")
        .when()
            .get("/users/123")
        .then()
            .statusCode(200)
            .body("id", equalTo(123))
            .body("email", notNullValue())
            .body("name", notNullValue());
    }

    @Test
    @DisplayName("Should return 404 when user not found")
    void shouldReturn404_whenUserNotFound() {
        given()
            .header("Authorization", "Bearer valid-token")
        .when()
            .get("/users/99999")
        .then()
            .statusCode(404)
            .body("error", equalTo("User not found"));
    }
}
