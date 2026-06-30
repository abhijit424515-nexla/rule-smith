package com.nexla.parser.xml;

import static com.ctc.wstx.api.WstxOutputProperties.P_OUTPUT_VALIDATE_STRUCTURE;
import static org.codehaus.stax2.XMLOutputFactory2.P_AUTOMATIC_EMPTY_ELEMENTS;

import com.bazaarvoice.jolt.JsonUtils;
import com.ctc.wstx.stax.WstxOutputFactory;
import com.nexla.json.JSONObject;
import com.nexla.json.XML;
import com.nexla.json.XMLParserConfiguration;
import java.io.Reader;
import java.io.StringWriter;
import java.util.*;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.XMLStreamWriter;
import lombok.SneakyThrows;
import one.util.streamex.EntryStream;
import org.apache.commons.lang.ArrayUtils;
import org.jetbrains.annotations.NotNull;

public final class XmlUtils {
  private static final String TEXT = "#text";
  private static final String ATTRIBUTE_PREFIX = "-";
  private static final String FLATTEN_LIST_PREFIX = "+";

  private static final XMLParserConfiguration XML_PARSER_CONFIGURATION =
      new XMLParserConfiguration()
          .withAttributePrefix(ATTRIBUTE_PREFIX)
          .withcDataTagName(TEXT)
          .withKeepStrings(true);

  public static LinkedHashMap<String, Object> toRawMessage(String xml) {
    return (LinkedHashMap<String, Object>) JsonUtils.jsonToMap(toJsonObject(xml).toString());
  }

  public static @NotNull JSONObject toJsonObject(String xml) {
    return XML.toJSONObject(xml, XML_PARSER_CONFIGURATION);
  }

  @SneakyThrows
  public static LinkedHashMap<String, Object> toRawMessage(Reader reader) {
    return (LinkedHashMap<String, Object>)
        JsonUtils.jsonToMap(XML.toJSONObject(reader, XML_PARSER_CONFIGURATION).toString());
  }

  public static String toXML(String rootTag, Map<String, Object> record) {
    return new NXml(false, ATTRIBUTE_PREFIX, FLATTEN_LIST_PREFIX, TEXT, false)
        .toXml(rootTag, record);
  }

  private static class NXml {
    private final boolean includeProlog;
    private final String attributePrefix;
    private final String flattenListPrefix;
    private final String textPropName;
    private final boolean alwaysSelfClose;

    public NXml(
        boolean includeProlog,
        String attributePrefix,
        String flattenListPrefix,
        String textPropName,
        boolean alwaysSelfClose) {
      this.includeProlog = includeProlog;
      this.attributePrefix = attributePrefix;
      this.flattenListPrefix = flattenListPrefix;
      this.textPropName = textPropName;
      this.alwaysSelfClose = alwaysSelfClose;
    }

    @SneakyThrows
    public String toXml(String rootName, Map<String, Object> o) {
      StringWriter dest = new StringWriter();
      WstxOutputFactory factory = new WstxOutputFactory();
      factory.setProperty(P_AUTOMATIC_EMPTY_ELEMENTS, alwaysSelfClose);
      // this allows multiple roots
      factory.setProperty(P_OUTPUT_VALIDATE_STRUCTURE, false);

      XMLStreamWriter w = factory.createXMLStreamWriter(dest);

      if (includeProlog) {
        w.writeStartDocument();
      }

      if (rootName == null) {
        o.forEach((k, v) -> elem(w, k, v));
      } else {
        elem(w, rootName, o);
      }

      w.writeEndDocument();

      w.flush();
      w.close();

      return dest.toString();
    }

    @SneakyThrows
    private void elem(XMLStreamWriter w, String name, Object value) {
      String local = norm(name);

      if (value == null) {
        // writer will automatically collapse tag if #alwaysSelfClose
        w.writeStartElement(local);
        w.writeEndElement();
        return;
      }

      if (value instanceof Collection || value.getClass().isArray()) {
        List<Object> values = toList(value);

        if (name.startsWith(flattenListPrefix)
            && !values.isEmpty()
            && values.get(0) instanceof Map) {
          w.writeStartElement(local);
          values.forEach(
              el -> {
                Map<String, Object> m = (Map<String, Object>) el;
                m.forEach((k, v) -> elem(w, k, v));
              });
          w.writeEndElement();
        } else {
          values.forEach(el -> elem(w, name, el));
        }
        return;
      }

      w.writeStartElement(local);
      if (value instanceof Map) {
        Map<String, Object> m = (Map<String, Object>) value;

        attributes(m).forEach((a, v) -> writeAttribute(w, a, v));

        // inner tags
        EntryStream.of(m)
            .removeKeys(k -> k.startsWith(attributePrefix))
            .removeKeys(textPropName::equals)
            .forEachOrdered(e -> elem(w, e.getKey(), e.getValue()));

        fst(m, textPropName).ifPresent(t -> writeCharacters(w, t));
      } else if (value instanceof Number || value instanceof String || value instanceof Boolean) {
        String text = value.toString();
        if (!text.isEmpty()) {
          w.writeCharacters(text);
        }
      }
      w.writeEndElement();
    }

    private List<Object> toList(Object value) {
      if (value.getClass().isArray()) {
        if (value instanceof byte[]) {
          return Arrays.asList(ArrayUtils.toObject((byte[]) value));
        } else if (value instanceof short[]) {
          return Arrays.asList(ArrayUtils.toObject((short[]) value));
        } else if (value instanceof int[]) {
          return Arrays.asList(ArrayUtils.toObject((int[]) value));
        } else if (value instanceof long[]) {
          return Arrays.asList(ArrayUtils.toObject((long[]) value));
        } else if (value instanceof float[]) {
          return Arrays.asList(ArrayUtils.toObject((float[]) value));
        } else if (value instanceof double[]) {
          return Arrays.asList(ArrayUtils.toObject((double[]) value));
        } else if (value instanceof boolean[]) {
          return Arrays.asList(ArrayUtils.toObject((boolean[]) value));
        } else if (value instanceof char[]) {
          return Arrays.asList(ArrayUtils.toObject((char[]) value));
        } else if (value instanceof Object[]) {
          return Arrays.asList((Object[]) value);
        }

        return Collections.emptyList();
      }

      if (value instanceof List) {
        return (List<Object>) value;
      }

      if (value instanceof Collection) {
        return new ArrayList<>((Collection<?>) value);
      }

      throw new RuntimeException(value + " is not a collection or an array");
    }

    private Map<String, String> attributes(Map<String, Object> m) {
      return EntryStream.of(m)
          .filterKeys(Objects::nonNull)
          .filterKeys(k -> k.startsWith(attributePrefix))
          .mapValues(String::valueOf)
          .toCustomMap(LinkedHashMap::new);
    }

    private Optional<String> fst(Map<String, Object> o, String propName) {
      if (o.isEmpty()) return Optional.empty();

      return EntryStream.of(o)
          .filterKeys(propName::equals)
          .values()
          .map(Object::toString)
          .findFirst();
    }

    private String norm(String name) {
      return name.replaceAll("[!\"#$%&'()*+,/;<=>?@\\[\\\\\\]^`{|}~]", "-")
          .replaceAll("\\s+", "_")
          .replaceAll("^([-.])+", "")
          .replaceAll("^(\\d+)", "_$1");
    }

    private void writeAttribute(XMLStreamWriter w, String a, String v) {
      try {
        w.writeAttribute(norm(a.substring(attributePrefix.length())), v);
      } catch (XMLStreamException e) {
        throw new RuntimeException(e);
      }
    }

    private void writeCharacters(XMLStreamWriter w, String t) {
      try {
        w.writeCharacters(t);
      } catch (XMLStreamException e) {
        throw new RuntimeException(e);
      }
    }
  }
}
