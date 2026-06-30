class DurationClean {
  long durationMs(int days) {
    long ms = (long) days * 24 * 60 * 60 * 1000;
    return ms;
  }
}
