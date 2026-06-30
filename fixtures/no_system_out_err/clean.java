import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class C {
  private static final Logger log = LoggerFactory.getLogger(C.class);

  void run(String msg) {
    log.info(msg);
  }
}
