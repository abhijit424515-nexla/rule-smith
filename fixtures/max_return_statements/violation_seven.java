public class SevenReturns {
  public String grade(int score) {
    if (score >= 95) {
      return "A+";
    }
    if (score >= 90) {
      return "A";
    }
    if (score >= 80) {
      return "B";
    }
    if (score >= 70) {
      return "C";
    }
    if (score >= 60) {
      return "D";
    }
    if (score >= 0) {
      return "F";
    }
    return "invalid";
  }
}
