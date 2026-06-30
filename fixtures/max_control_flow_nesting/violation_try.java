class Sample {
  void run(int n) {
    for (int a = 0; a < n; a++) {
      while (a < 5) {
        if (a % 2 == 0) {
          try {
            if (a > 0) {
              System.out.println(a);
            }
          } catch (RuntimeException e) {
            System.out.println("err");
          }
        }
        a++;
      }
    }
  }
}
