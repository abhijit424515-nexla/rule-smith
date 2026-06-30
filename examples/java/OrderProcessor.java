package examples;

import java.util.Optional;

public class OrderProcessor {

  enum Status {
    NEW,
    PAID,
    SHIPPED
  }

  String route(Status status) {
    switch (status) { // enum-switch-default: no default
      case NEW:
        return "create";
      case PAID:
        return "fulfil";
      case SHIPPED:
        return "track";
    }
    return "";
  }

  String customerName(long id) {
    Optional<String> name = lookup(id); // optional-get-without-ispresent
    return name.get();
  }

  boolean sameQty(int a0, int b0) {
    Integer a = Integer.valueOf(a0); // boxed-integer-long-comparison
    Integer b = Integer.valueOf(b0);
    return a == b;
  }

  Optional<String> lookup(long id) {
    return Optional.empty();
  }
}
