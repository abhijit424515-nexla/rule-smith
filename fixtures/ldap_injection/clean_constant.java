import javax.naming.directory.*;

public class StaticSearch {
  public NamingEnumeration<SearchResult> all(DirContext ctx) throws Exception {
    SearchControls controls = new SearchControls();
    return ctx.search("ou=users", "(objectClass=person)", controls);
  }
}
