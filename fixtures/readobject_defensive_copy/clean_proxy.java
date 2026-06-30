import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import java.util.Date;

public class Period implements Serializable {
  private Date start;
  private Date end;

  public Period(Date start, Date end) {
    this.start = new Date(start.getTime());
    this.end = new Date(end.getTime());
  }

  private Object writeReplace() {
    return new SerializationProxy(this);
  }

  private void readObject(ObjectInputStream s) throws InvalidObjectException {
    throw new InvalidObjectException("Proxy required");
  }

  private static class SerializationProxy implements Serializable {
    private final Date start;
    private final Date end;

    SerializationProxy(Period p) {
      this.start = p.start;
      this.end = p.end;
    }

    private Object readResolve() {
      return new Period(start, end);
    }
  }
}
