class Service {
  public void load() {
    try {
      open();
    } catch (Exception e) {
      recover();
    }
  }
}
