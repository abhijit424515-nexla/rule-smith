class Service {
  private final Conn conn;

  Service(Conn c) {
    this.conn = c;
  }

  void run() {
    if (this.conn != null) {
      this.conn.send();
    }
  }
}
