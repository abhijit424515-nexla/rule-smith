public class C {
  void f() {
    try {
      risky();
    } catch (Exception e) {
      throw new RuntimeException("failed", e);
    }
  }

  void risky() {}
}
