package com.nexla.probe.pinecone;

import static com.bazaarvoice.jolt.JsonUtils.jsonToMap;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import io.pinecone.proto.Vector;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import one.util.streamex.StreamEx;

public class PineconeHelper {

  public static Object extractMetadataValue(Value metadata) {
    switch (metadata.getKindCase()) {
      case STRING_VALUE:
        return metadata.getStringValue();
      case BOOL_VALUE:
        return metadata.getBoolValue();
      case NULL_VALUE:
        return null;
      case NUMBER_VALUE:
        return metadata.getNumberValue();
      case STRUCT_VALUE:
        return extractMetadataStruct(metadata.getStructValue());
      case LIST_VALUE:
        return extractMetadataList(metadata.getListValue());
      default:
        throw new IllegalArgumentException(
            "Unsupported metadata value type: " + metadata.getKindCase());
    }
  }

  public static Map<String, Object> extractMetadataStruct(Struct struct) {
    if (struct == null) {
      return null;
    }
    return StreamEx.of(struct.getFieldsMap().entrySet())
        .toSortedMap(Map.Entry::getKey, entry -> extractMetadataValue(entry.getValue()));
  }

  public static List<Object> extractMetadataList(ListValue listValue) {
    return listValue.getValuesList().stream()
        .map(PineconeHelper::extractMetadataValue)
        .collect(Collectors.toList());
  }

  public static Optional<Map<String, Object>> extractMetadata(Vector vector) {
    if (vector.hasMetadata()) {
      return Optional.of(
          StreamEx.of(vector.getMetadata().getFieldsMap().entrySet())
              .toSortedMap(Map.Entry::getKey, entry -> extractMetadataValue(entry.getValue())));
    } else {
      return Optional.empty();
    }
  }

  public static Struct createFilterFromJsonString(String jsonFilter) {
    if (jsonFilter == null) {
      return null;
    }

    try {
      var filterMap = jsonToMap(jsonFilter);
      return convertMap(filterMap);
    } catch (Exception e) {
      throw new RuntimeException("Error parsing Pinecone JSON filter", e);
    }
  }

  public static Struct convertMap(Map<String, Object> map) {
    var struct = Struct.newBuilder();

    map.entrySet().stream()
        .forEach(
            entry -> {
              struct.putFields(entry.getKey(), convertValue(entry.getValue()));
            });

    return struct.build();
  }

  private static ListValue convertList(List<Object> list) {
    var listValue = ListValue.newBuilder();

    list.stream()
        .forEach(
            value -> {
              listValue.addValues(convertValue(value));
            });

    return listValue.build();
  }

  private static Value convertValue(Object value) {
    if (value instanceof String) {
      return Value.newBuilder().setStringValue((String) value).build();
    } else if (value instanceof Number) {
      return Value.newBuilder().setNumberValue(((Number) value).doubleValue()).build();
    } else if (value instanceof Boolean) {
      return Value.newBuilder().setBoolValue((Boolean) value).build();
    } else if (value instanceof Map) {
      return Value.newBuilder().setStructValue(convertMap((Map<String, Object>) value)).build();
    } else if (value instanceof List) {
      return Value.newBuilder().setListValue(convertList((List<Object>) value)).build();
    } else if (value == null) {
      return Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build();
    } else {
      throw new IllegalArgumentException("Unsupported value type: " + value.getClass());
    }
  }
}
