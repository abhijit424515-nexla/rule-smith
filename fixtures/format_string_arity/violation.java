public class Report {
  String line(String name, int count) {
    return String.format("%s = %d, total %d", name, count);
  }
}
