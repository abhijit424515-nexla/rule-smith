import javax.naming.directory.*;

public class UserSearch {
  public NamingEnumeration<SearchResult> find(DirContext ctx, String username) throws Exception {
    SearchControls controls = new SearchControls();
    return ctx.search("ou=users", "(uid=" + username + ")", controls);
  }
}
