class ReportService {
  void run(Wallet w, Logger log) {
    if (w.getBalance() < 0) {
      log.setError(true);
    }
  }
}
