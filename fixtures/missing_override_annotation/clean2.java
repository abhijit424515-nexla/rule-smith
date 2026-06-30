class OverrideClean2 {
  static class Base {
    void greet() {}
  }

  static class Derived extends Base {
    void farewell() {
      System.out.println("bye");
    }

    void greet(int times) {
      System.out.println(times);
    }
  }
}
