import java.text.SimpleDateFormat;
import java.util.Date;

class Reports {
  private static final ThreadLocal<SimpleDateFormat> FMT =
      ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

  String fmt(Date d) {
    return FMT.get().format(d);
  }
}
