class DurationOverflow {
  long durationMs(int days) {
    long ms = days * 24 * 60 * 60 * 1000;
    return ms;
  }
}
