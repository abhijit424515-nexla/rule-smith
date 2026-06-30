package examples;

import java.io.InputStream;
import java.util.Map;
import java.util.Optional;
import javax.annotation.concurrent.GuardedBy;

// Every method here is syntactically ordinary. The defect lives in the CONTROL
// or DATA FLOW -- the same tokens are a bug on one path and correct on another.
// A flat "always close streams / always guard Optional / lock shared state"
// rule pasted into CLAUDE.md cannot see the difference. RuleSmith can, because
// each check runs a real CFG + dominance / post-dominance analysis.
public class PaymentGateway {

  @GuardedBy("this")
  private long retries; // shared mutable state

  private final String region;

  // (1) field-read-before-assign: this.region read before it is assigned
  PaymentGateway(String r) {
    int n = this.region.length();
    this.region = r;
  }

  // (2) resource-leak: close() is present but an early return skips it
  void pull(boolean dryRun) {
    InputStream in = open();
    if (dryRun) {
      return;
    }
    in.close();
  }

  // (3) optional-get-without-ispresent: get() not dominated by isPresent()
  String account(long id) {
    Optional<String> acct = lookup(id);
    return acct.get();
  }

  // (4) null-deref-needs-dominating-guard: guard misses one path to the deref
  int tokenLength(Map<String, String> m, String k) {
    String s = null;
    if (m.containsKey(k)) {
      s = m.get(k);
    }
    return s.length();
  }

  // (5) unchecked-downcast: cast not guarded by a dominating instanceof
  String describe(Object o) {
    return ((String) o).trim();
  }

  // (6) non-atomic-shared-update: read-modify-write on @GuardedBy field
  void bump() {
    retries = retries + 1;
  }

  // (7) guarded-by-lock-held: @GuardedBy field read without holding the lock
  long readRetries() {
    return retries;
  }

  // (8) no-string-concat-in-loop: O(n^2) string building
  String join(String[] parts) {
    String out = "";
    for (String p : parts) {
      out += p;
    }
    return out;
  }

  // (9) no-superfluous-else: else after a branch that always returns
  String classify(int code) {
    if (code < 0) {
      return "neg";
    } else {
      return "nonneg";
    }
  }

  InputStream open() {
    return null;
  }

  Optional<String> lookup(long id) {
    return Optional.empty();
  }
}
