import java.io.InputStream;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamReader;

public class CleanXif {
  public XMLStreamReader read(InputStream in) throws Exception {
    XMLInputFactory xif = XMLInputFactory.newInstance();
    xif.setProperty(XMLInputFactory.SUPPORT_DTD, false);
    xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
    return xif.createXMLStreamReader(in);
  }
}
