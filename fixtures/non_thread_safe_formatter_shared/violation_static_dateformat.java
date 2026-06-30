import java.text.SimpleDateFormat;
import java.util.Date;

class Reports {
  private static final SimpleDateFormat FMT = new SimpleDateFormat("yyyy-MM-dd");

  String fmt(Date d) {
    return FMT.format(d);
  }
}
