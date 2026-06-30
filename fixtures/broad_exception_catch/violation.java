class A {
  void run(Runnable r) {
    try {
      r.run();
    } catch (Exception e) {
      System.out.println("oops");
    }
  }
}
