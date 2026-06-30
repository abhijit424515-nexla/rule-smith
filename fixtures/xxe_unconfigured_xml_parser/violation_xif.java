import java.io.InputStream;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamReader;

public class ViolationXif {
  public XMLStreamReader read(InputStream in) throws Exception {
    XMLInputFactory xif = XMLInputFactory.newInstance();
    return xif.createXMLStreamReader(in);
  }
}
