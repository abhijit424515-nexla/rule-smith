class OverrideViolation2 {
  interface Runner {
    void run(int n);
  }

  static class Worker implements Runner {
    public void run(int n) {
      System.out.println(n);
    }
  }
}
