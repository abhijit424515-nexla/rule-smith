class UsesUnsignedHelpers {
  int h(@Unsigned int x, @Unsigned int y) {
    return Integer.divideUnsigned(x, y);
  }
}
