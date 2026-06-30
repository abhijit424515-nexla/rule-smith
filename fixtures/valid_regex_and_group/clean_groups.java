import java.util.regex.Matcher;
import java.util.regex.Pattern;

class CleanGroups {
  String parse(String s) {
    Pattern p = Pattern.compile("(\\d+)-(\\d+)");
    Matcher m = p.matcher(s);
    if (m.matches()) {
      return m.group(0) + m.group(1) + m.group(2);
    }
    return null;
  }
}
