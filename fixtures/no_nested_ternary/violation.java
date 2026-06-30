class Grade {
  String letter(int score) {
    return score >= 90 ? "A" : score >= 80 ? "B" : "C";
  }
}
