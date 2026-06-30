class Counter {
  private int count;

  public int incrementAndGet() {
    this.count = this.count + 1;
    return this.count;
  }
}
