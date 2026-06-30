class Report {
  private String prefix;

  String build(Customer c) {
    log();
    return c.getName() + c.getAddress() + c.getEmail() + c.getPhone();
  }

  void log() {}
}
