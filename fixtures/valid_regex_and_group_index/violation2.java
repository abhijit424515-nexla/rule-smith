import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class GroupIndexOob {
  String third(String s) {
    Pattern p = Pattern.compile("(\\d+)-(\\d+)");
    Matcher m = p.matcher(s);
    if (m.matches()) {
      return m.group(3);
    }
    return null;
  }
}
