class A {
  void m(int x) {
    switch (x) {
      case 1 -> foo();
      case 2 -> bar();
      default -> baz();
    }
  }
}
