class OverrideClean {
  static class Base {
    void greet() {}
  }

  static class Derived extends Base {
    @Override
    void greet() {
      System.out.println("hi");
    }
  }
}
