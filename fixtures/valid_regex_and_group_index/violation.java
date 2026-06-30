public class RegexCompileBroken {
  java.util.regex.Pattern build() {
    return java.util.regex.Pattern.compile("(unterminated");
  }
}
