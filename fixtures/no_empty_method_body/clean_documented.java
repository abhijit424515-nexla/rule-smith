public class Qux {
  @Override
  public void onEvent() {
    // intentionally empty: events are ignored in this handler
  }

  native void fromC();
}
