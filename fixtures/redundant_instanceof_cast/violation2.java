class NumStr {
  String describe(Object x) {
    if (x instanceof Number) {
      Number n = (Number) x;
      return n.toString();
    }
    return "";
  }
}
