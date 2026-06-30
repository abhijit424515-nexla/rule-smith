class BarTest {
  public void testParseFails() {
    try {
      Integer.parseInt("x");
    } catch (NumberFormatException e) {
      log(e);
    }
  }
}
