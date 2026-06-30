class V2 {
  String widen(Object a, Object b) {
    if (b instanceof String) {
      return ((String) a).trim();
    }
    return "";
  }
}
