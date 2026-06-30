import java.text.SimpleDateFormat;
import java.util.Date;

class Reports {
  String fmt(Date d) {
    SimpleDateFormat local = new SimpleDateFormat("yyyy-MM-dd");
    return local.format(d);
  }
}
