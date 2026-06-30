import java.util.logging.Logger;

public class D {
  static final Logger log = Logger.getLogger("D");

  int h() {
    int x = -1;
    try {
      x = compute();
    } catch (Exception e) {
      log.warning("compute failed: " + e);
      x = 0;
    }
    return x;
  }

  int compute() {
    return 1;
  }
}
