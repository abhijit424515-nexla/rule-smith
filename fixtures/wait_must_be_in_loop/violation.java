class WaitOutsideLoop {
  private boolean ready;

  synchronized void awaitReady() throws InterruptedException {
    if (!ready) {
      wait();
    }
    process();
  }

  void process() {}
}
