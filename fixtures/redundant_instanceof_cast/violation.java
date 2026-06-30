class StringLen {
  int len(Object o) {
    if (o instanceof String) {
      String s = (String) o;
      return s.length();
    }
    return 0;
  }
}
