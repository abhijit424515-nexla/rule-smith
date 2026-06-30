class C {
  void h() {
    try {
      risky();
    } catch (java.io.IOException e) {
      log(e);
    }
  }
}
