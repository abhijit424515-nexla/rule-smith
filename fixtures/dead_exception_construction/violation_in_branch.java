class DeadThrowInBranch {
  void validate(int x) {
    if (x < 0) {
      new IllegalArgumentException("negative input");
    }
  }
}
