public class Pinger {
  void ping(String[] args) throws Exception {
    String host = args[0];
    ProcessBuilder pb = new ProcessBuilder("ping", host);
    pb.start();
  }
}
