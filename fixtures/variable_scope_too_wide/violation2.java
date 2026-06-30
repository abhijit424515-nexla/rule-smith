class B {
  void g(int[] a) {
    int total = 0;
    for (int i = 0; i < a.length; i++) {
      total += a[i];
      System.out.println(total);
    }
  }
}
