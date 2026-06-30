class UserService {
  User validateUser(String raw) {
    if (raw == null) {
      throw new IllegalArgumentException("null");
    }
    return new User(raw);
  }
}
