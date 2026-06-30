public class Holder {
  private int myField = 0;
  private final int myFinalField = 1;
  private static int myStaticField = 2;

  public int total() {
    return myField + myFinalField + myStaticField;
  }
}
