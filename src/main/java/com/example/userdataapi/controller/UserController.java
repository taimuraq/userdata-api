package com.example.userdataapi.controller;

import com.example.userdataapi.model.User;
import com.example.userdataapi.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@Tag(name = "User", description = "User management APIs")
public class UserController {

  private final UserService userService;

  public UserController(UserService userService) {
    this.userService = userService;
  }
  @Operation(summary = "Create a new user")
  @ApiResponse(responseCode = "200", description = "User created")
  @PostMapping
  public User createUser(@RequestBody User user) {
    return userService.createUser(user);
  }

  @Operation(summary = "Get a user by ID")
  @ApiResponse(responseCode = "200", description = "User found")
  @ApiResponse(responseCode = "404", description = "User not found")
  @GetMapping("/{id}")
  public User getUserById(@PathVariable String id) {
    return userService.getUserById(id);
  }

  @Operation(summary = "Update a user")
  @ApiResponse(responseCode = "200", description = "User updated")
  @PutMapping("/{id}")
  public User updateUser(@PathVariable String id, @RequestBody User user) {
    user.setId(id);
    return userService.updateUser(id, user);
  }
}

