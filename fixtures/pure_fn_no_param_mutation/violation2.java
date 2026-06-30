public class ViolationArrayAndField {
  static class Box {
    int value;
  }

  public int sumValues(int[] data, Box box) {
    data[0] = 0;
    box.value = 7;
    return data[0];
  }
}
