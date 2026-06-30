class AgeService {
  void validateAge(int age) {
    if (age < 0) {
      throw new IllegalArgumentException("negative age");
    }
  }
}
