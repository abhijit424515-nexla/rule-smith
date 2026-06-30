class Sizer {
  int size(String s) {
    switch (s.length()) {
      case 0:
        return 0;
      case 1:
        return 1;
    }
    return -1;
  }
}
