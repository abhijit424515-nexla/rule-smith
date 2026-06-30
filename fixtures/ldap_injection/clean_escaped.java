import javax.naming.directory.*;
import org.springframework.ldap.support.LdapEncoder;

public class SafeSearch {
  public NamingEnumeration<SearchResult> find(DirContext ctx, String username) throws Exception {
    SearchControls controls = new SearchControls();
    String filter = "(uid=" + LdapEncoder.filterEncode(username) + ")";
    return ctx.search("ou=users", filter, controls);
  }
}
