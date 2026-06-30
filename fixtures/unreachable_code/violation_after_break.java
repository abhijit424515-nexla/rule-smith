class AfterBreak {
  void loop() {
    for (int i = 0; i < 3; i++) {
      break;
      doWork();
    }
  }

  void doWork() {}
}
