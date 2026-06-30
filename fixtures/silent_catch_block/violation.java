public class A {
  void f() {
    try {
      risky();
    } catch (Exception e) {
    }
  }

  void risky() {}
}
