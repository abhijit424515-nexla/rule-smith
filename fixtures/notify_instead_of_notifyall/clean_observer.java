public class EventBus {
  private Listener observer;

  public void emit(Event event) {
    observer.notify(event);
  }

  interface Listener {
    void notify(Event e);
  }
}
