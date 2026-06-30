class V2 {
  void run() throws Exception {
    try {
      risky();
    } catch (Exception e) {
      throw e;
    } finally {
      throw new IllegalStateException("cleanup");
    }
  }

  void risky() throws Exception {}
}
