class WaitInWhile {
  private boolean ready;

  synchronized void awaitReady() throws InterruptedException {
    while (!ready) {
      wait();
    }
    process();
  }

  void process() {}
}
