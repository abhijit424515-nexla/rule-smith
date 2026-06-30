package examples;

import java.io.InputStream;
import java.util.Map;
import java.util.Optional;
import javax.annotation.concurrent.GuardedBy;

// Same code, every control/data-flow defect repaired. RuleSmith now reports
// zero findings for the ten flow-sensitive rules.
public class PaymentGateway {

  @GuardedBy("this")
  private long retries = 0;

  private final String region;

  // (1) assign before any read; field definitely assigned on the only path
  PaymentGateway(String r) {
    this.region = r;
  }

  // (2) try-with-resources closes on every exit, dry-run or not
  void pull(boolean dryRun) {
    try (InputStream in = open()) {
      if (dryRun) {
        return;
      }
      use(in);
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  // (3) orElse instead of an unguarded get()
  String account(long id) {
    return lookup(id).orElse("unknown");
  }

  // (4) deref only on the path where the value is present
  int tokenLength(Map<String, String> m, String k) {
    if (m.containsKey(k)) {
      return m.get(k).length();
    }
    return 0;
  }

  // (5) cast guarded by a dominating instanceof
  String describe(Object o) {
    if (o instanceof String) {
      return ((String) o).trim();
    }
    return "";
  }

  // (6) compound update under the monitor
  synchronized void bump() {
    retries = retries + 1;
  }

  // (7) read under the same lock
  synchronized long readRetries() {
    return retries;
  }

  // (8) StringBuilder, linear
  String join(String[] parts) {
    StringBuilder out = new StringBuilder();
    for (String p : parts) {
      out.append(p);
    }
    return out.toString();
  }

  // (9) no else after a returning branch
  String classify(int code) {
    if (code < 0) {
      return "neg";
    }
    return "nonneg";
  }

  InputStream open() {
    return null;
  }

  void use(InputStream in) {}

  Optional<String> lookup(long id) {
    return Optional.empty();
  }
}
