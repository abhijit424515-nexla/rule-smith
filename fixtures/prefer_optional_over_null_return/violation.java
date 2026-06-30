class UserRepo {
  String findName(int id) {
    if (id < 0) {
      return null;
    }
    return "alice";
  }
}
