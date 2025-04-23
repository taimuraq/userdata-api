package com.example.userdataapi.dao;


import com.example.userdataapi.model.User;
import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class UserDao {

  private final Map<String, User> users = new ConcurrentHashMap<>();

  public UserDao() {
    // Mock data
    users.put("1", new User("1", "Alice", "alice@example.com"));
    users.put("2", new User("2", "Bob", "bob@example.com"));
  }

  public User getUserById(String id) {
    return users.get(id);
  }

  public User createUser(User user) {
    users.put(user.getId(), user);
    return user;
  }

  public User updateUser(String id, User user) {
    users.put(id, user);
    return user;
  }
}

