import java.util.regex.Matcher;
import java.util.regex.Pattern;

class Validator {
  private final Matcher matcher = Pattern.compile("\\d+").matcher("");

  boolean ok(String s) {
    return matcher.reset(s).matches();
  }
}
