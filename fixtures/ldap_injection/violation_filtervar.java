import javax.servlet.http.HttpServletRequest;
import org.springframework.ldap.core.LdapTemplate;

public class LdapAuth {
  private LdapTemplate ldapTemplate;

  public Object lookup(HttpServletRequest request) {
    String user = request.getParameter("user");
    String filter = "(&(objectClass=person)(cn=" + user + "))";
    return ldapTemplate.search("", filter, null);
  }
}
