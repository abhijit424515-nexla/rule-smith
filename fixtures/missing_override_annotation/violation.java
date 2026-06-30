class OverrideViolation {
  static class Base {
    void greet() {}
  }

  static class Derived extends Base {
    void greet() {
      System.out.println("hi");
    }
  }
}
