class A {
  void m(String s) {
    try {
      s.length();
    } catch (NullPointerException e) {
      System.out.println("oops");
    }
  }
}
