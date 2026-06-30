import java.text.SimpleDateFormat;
import java.util.Date;

class Reports {
  private final SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd");

  synchronized String format(Date d) {
    return fmt.format(d);
  }

  synchronized Date parse(String s) throws Exception {
    return fmt.parse(s);
  }
}
