package examples;

import java.util.Optional;

public class OrderProcessor {

  enum Status {
    NEW,
    PAID,
    SHIPPED
  }

  String route(Status status) {
    switch (status) {
      case NEW:
        return "create";
      case PAID:
        return "fulfil";
      case SHIPPED:
        return "track";
      default:
        return "unknown"; // fixed: enum-switch-default
    }
  }

  String customerName(long id) {
    Optional<String> name = lookup(id);
    return name.orElse("anonymous"); // fixed: optional-get-without-ispresent
  }

  boolean sameQty(int a0, int b0) {
    Integer a = Integer.valueOf(a0);
    Integer b = Integer.valueOf(b0);
    return a.equals(b); // fixed: boxed-integer-long-comparison
  }

  Optional<String> lookup(long id) {
    return Optional.empty();
  }
}
