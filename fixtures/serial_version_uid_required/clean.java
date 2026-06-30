package x;

import java.io.Serializable;

public class Box implements Serializable {
  private static final long serialVersionUID = 42L;
  private int n;

  public int get() {
    return n;
  }
}
