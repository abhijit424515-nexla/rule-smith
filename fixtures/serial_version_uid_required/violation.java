package x;

import java.io.Serializable;

public class Account implements Serializable {
  private String owner;

  public Account(String o) {
    this.owner = o;
  }
}
