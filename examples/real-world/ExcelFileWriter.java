package com.nexla.writer;

import static com.nexla.common.parse.ParserConfigs.Csv.WRITE_HEADER;
import static com.nexla.common.parse.ParserConfigs.Excel.EXCEL_SHEET;
import static com.nexla.common.parse.ParserConfigs.Excel.EXCEL_XLSX;
import static com.nexla.common.parse.ParserConfigs.Excel.EXCEL_XLSX_COMPRESS_TEMP;

import com.google.common.collect.Maps;
import com.nexla.connector.config.MappingConfig;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.StringWriter;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import lombok.SneakyThrows;
import one.util.streamex.EntryStream;
import one.util.streamex.StreamEx;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

public class ExcelFileWriter extends BinaryBase {

  @Override
  public int getDefaultBufferedWriterSize() {
    return 32 * 1024; // 32KB
  }

  public static final String DEFAULT_SHEET = "Sheet1";

  private boolean needWriteHeader = true;
  private Boolean compressTempFile = false;
  private String sheetName;
  private LinkedHashSet<String> mappingFields = null;

  @Override
  public int append(Map<String, Object> record, Optional<MappingConfig> mappingConfig) {
    // Simple fix to write records according to the provided schema. Possibly we will need to
    // improve the approach in future.
    if (mappingFields == null) {
      mappingConfig.ifPresent(
          mapping -> mappingFields = new LinkedHashSet<>(mapping.getFieldsOrder()));
    }
    return super.append(record, mappingConfig);
  }

  private int writeRecord(
      Map<String, Object> record,
      SXSSFSheet sheet,
      AtomicInteger rowNum,
      Map<String, Integer> headers) {
    Row row = sheet.createRow(rowNum.getAndIncrement());
    AtomicInteger skipHeaderIncrementalCell = new AtomicInteger(0);
    return EntryStream.of(record)
        .mapKeyValue(
            (key, value) -> {
              Integer idx = headers.get(key);
              if (idx == null) {
                if (needWriteHeader) {
                  logger.warn(
                      "Record field {} is not present in schema. Skipping the value: {}",
                      key,
                      value);
                  return 0;
                } else {
                  idx = skipHeaderIncrementalCell.getAndAdd(1);
                }
              }
              Cell cell = row.createCell(idx);
              cell.setCellValue(value.toString());
              return value.toString().getBytes().length;
            })
        .mapToInt(x -> x)
        .sum();
  }

  @SneakyThrows
  @Override
  protected void writeStreamOnFinish(StreamEx<LinkedHashMap<String, Object>> messageStream) {
    File file = new File(outputPath);
    String name = sheetName != null ? sheetName : DEFAULT_SHEET;
    try (FileOutputStream fos = new FileOutputStream(file);
        SXSSFWorkbook workbook = new SXSSFWorkbook()) {
      SXSSFSheet sheet = workbook.createSheet(name);
      workbook.setCompressTempFiles(compressTempFile);

      AtomicInteger rowNum = new AtomicInteger(0);

      Iterator<LinkedHashMap<String, Object>> messagesIter = messageStream.iterator();
      if (messagesIter.hasNext()) {
        Map<String, Object> firstRecord = messagesIter.next();
        Map<String, Integer> headers = writeHeaders(sheet, rowNum, firstRecord);
        writeRecord(firstRecord, sheet, rowNum, headers);

        messagesIter.forEachRemaining(record -> writeRecord(record, sheet, rowNum, headers));

        workbook.write(fos);
        workbook.close();
        fos.flush();
        fos.close();
      }
    }
  }

  private Map<String, Integer> writeHeaders(
      SXSSFSheet sheet, AtomicInteger rowNum, Map<String, Object> record) {
    Map<String, Integer> headers = Maps.newHashMap();
    AtomicInteger number = new AtomicInteger(0);
    if (mappingFields != null) {
      mappingFields.forEach(fieldName -> headers.put(fieldName, number.getAndIncrement()));
    } else {
      record.forEach((k, v) -> headers.put(k, number.getAndIncrement()));
    }

    customHeader.ifPresent(
        ch -> {
          StringWriter customHeader = new StringWriter();
          writeCustomHeader(customHeader, record);
          addCustomHeaderToSheet(customHeader.toString(), sheet, rowNum);
        });
    if (needWriteHeader) {
      writeHeader(sheet, rowNum, headers);
    }
    return headers;
  }

  private void addCustomHeaderToSheet(String header, SXSSFSheet sheet, AtomicInteger rowNum) {
    Row row = sheet.createRow(rowNum.getAndIncrement());
    Cell cell = row.createCell(0);
    cell.setCellValue(header);
  }

  private void writeHeader(SXSSFSheet sheet, AtomicInteger rowNum, Map<String, Integer> headers) {
    Row row = sheet.createRow(rowNum.getAndIncrement());
    headers.forEach((name, idx) -> row.createCell(idx).setCellValue(name));
  }

  @Override
  public ExcelFileWriter option(String key, Object value) {

    super.option(key, value);

    switch (key) {
      case WRITE_HEADER:
        this.needWriteHeader = Boolean.valueOf(value.toString());
        break;
      case EXCEL_XLSX_COMPRESS_TEMP:
        this.compressTempFile = Boolean.valueOf(value.toString());
        break;
      case EXCEL_SHEET:
        this.sheetName = value.toString();
        break;
    }
    return this;
  }

  @Override
  public String getExtension() {
    return EXCEL_XLSX;
  }

  @SneakyThrows
  public static void mergeExcelFiles(File existingFile, File newFile) {

    Workbook existingWorkbook = new XSSFWorkbook(new FileInputStream(existingFile));
    Workbook newWorkbook = new XSSFWorkbook(new FileInputStream(newFile));

    Sheet existingSheet = existingWorkbook.getSheetAt(0);
    Sheet sheetToCopy = newWorkbook.getSheetAt(0);

    int lastRowNum = existingSheet.getLastRowNum();

    for (Row row : sheetToCopy) {
      Row newRow = existingSheet.createRow(++lastRowNum);

      for (Cell cell : row) {
        Cell newCell = newRow.createCell(cell.getColumnIndex(), cell.getCellType());
        newCell.setCellValue(cell.toString());
      }
    }

    FileOutputStream outputStream = new FileOutputStream(existingFile);
    existingWorkbook.write(outputStream);

    outputStream.close();
    existingWorkbook.close();
    newWorkbook.close();
  }
}
