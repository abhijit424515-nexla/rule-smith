public class Door {
  enum State {
    OPEN,
    CLOSED
  }

  public void set(State state, String label) {
    System.out.println(state + label);
  }
}
