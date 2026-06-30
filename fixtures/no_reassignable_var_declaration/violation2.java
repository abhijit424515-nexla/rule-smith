class Greeter {
  String build() {
    final var name = greeting();
    return name;
  }

  private String greeting() {
    return "hi";
  }
}
