class Cache {
  private java.util.Map<String, String> store;

  String get(String k) {
    if (store != null) {
      return store.get(k);
    }
    return null;
  }
}
