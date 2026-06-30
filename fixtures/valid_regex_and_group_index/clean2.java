public class StringRegexOk {
  String[] fields(String s) {
    return s.split("\\s*,\\s*");
  }

  boolean isLower(String s) {
    return s.matches("[a-z]+");
  }
}
