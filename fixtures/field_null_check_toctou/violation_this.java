class Service {
  private Conn conn;

  void run() {
    if (this.conn != null) {
      this.conn.send();
    }
  }
}
