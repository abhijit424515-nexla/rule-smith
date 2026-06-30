class Cache {
  private Object value = null;

  boolean missing() {
    return value == null;
  }
}
