class CleanInline {
  boolean check(String s) {
    return s.matches("[a-z]+") && s.split(",").length > 0;
  }
}
