class D {
  void m() {
    try {
      risky();
    } catch (IllegalArgumentException e) {
      recover();
    }
  }
  void risky() {}
  void recover() {}
}
