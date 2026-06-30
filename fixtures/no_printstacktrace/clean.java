public class C {
  private final Logger log = LoggerFactory.getLogger(C.class);

  void f() {
    try {
      g();
    } catch (Exception e) {
      log.error("g failed", e);
    }
  }
}
