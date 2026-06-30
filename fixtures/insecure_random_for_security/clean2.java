public class Backoff {
  double jitter() {
    double delay = Math.random() * 100.0;
    return delay;
  }
}
