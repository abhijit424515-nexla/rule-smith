class ReturnedException {
  Exception build() {
    Exception e = new RuntimeException("oops");
    return e;
  }
}
