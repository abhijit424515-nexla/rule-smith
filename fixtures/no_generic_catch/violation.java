class A {
  void f() {
    try {
      risky();
    } catch (Exception e) {
      log(e);
    }
  }
}
