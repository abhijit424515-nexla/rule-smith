class C {
  void h() {
    try {
      throw new IllegalArgumentException("in try is fine");
    } catch (IllegalArgumentException e) {
      throw new RuntimeException("in catch is fine", e);
    } finally {
      close();
    }
  }
}
