class Cache {
  private java.util.Map<String, String> store;

  String get(String k) {
    java.util.Map<String, String> local = store;
    if (local != null) {
      return local.get(k);
    }
    return null;
  }
}
