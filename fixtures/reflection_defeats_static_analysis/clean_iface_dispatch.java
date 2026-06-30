public class Service {
  interface Handler {
    String handle(String in);
  }

  String process(Handler h, String in) {
    return h.handle(in).trim();
  }
}
