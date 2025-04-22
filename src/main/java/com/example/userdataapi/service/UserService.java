package com.example.userdataapi.service;

import com.example.userdataapi.dao.UserDao;
import com.example.userdataapi.model.User;
import org.springframework.stereotype.Service;

@Service
public class UserService {

  private final UserDao userDao;

  public UserService(UserDao userDao) {
    this.userDao = userDao;
  }

  public User getUserById(String id) {
    return userDao.getUserById(id);
  }

  public User createUser(User user) {
    return userDao.createUser(user);
  }

  public User updateUser(String id, User user) {
    return userDao.updateUser(id, user);
  }
}

