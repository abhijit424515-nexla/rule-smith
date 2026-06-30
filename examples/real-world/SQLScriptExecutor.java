package com.nexla.script_runner.service;

import static com.nexla.common.StreamUtils.toLinkedHashMap;
import static one.util.streamex.EntryStream.zip;

import com.google.common.collect.Lists;
import com.nexla.common.Resource;
import com.nexla.common.notify.monitoring.NexlaMonitoringLogSeverity;
import connect.jdbc.util.JdbcUtils;
import java.io.BufferedReader;
import java.io.Reader;
import java.sql.*;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import lombok.Setter;
import lombok.SneakyThrows;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Setter
public class SQLScriptExecutor {

  private static final Logger LOGGER = LoggerFactory.getLogger(SQLScriptExecutor.class);
  private static final String LINE_SEPARATOR = System.lineSeparator();
  private static final String DEFAULT_DELIMITER = ";";
  private static final Pattern DELIMITER_PATTERN =
      Pattern.compile(
          "^\\s*((--)|(//))?\\s*(//)?\\s*@DELIMITER\\s+([^\\s]+)", Pattern.CASE_INSENSITIVE);

  private final Connection connection;

  private boolean catchResults;
  private boolean throwWarning;
  private boolean autoCommit;
  private boolean removeCRs;
  private boolean escapeProcessing = true;
  private Resource resource;
  private InsightsLogsPublisher insightsLogsPublisher;

  private String delimiter = DEFAULT_DELIMITER;
  private boolean fullLineDelimiter;

  public SQLScriptExecutor(
      Resource resource,
      boolean catchResults,
      Connection connection,
      InsightsLogsPublisher insightsLogsPublisher) {
    this.resource = resource;
    this.catchResults = catchResults;
    this.connection = connection;
    this.insightsLogsPublisher = insightsLogsPublisher;
  }

  public Optional<List<Map<String, String>>> runScript(Reader reader, AtomicInteger upd) {
    setAutoCommit();

    try {
      return executeLineByLine(reader, upd);
    } catch (Exception e) {
      LOGGER.error("[{}] Error executing SQL script", resource, e);
      insightsLogsPublisher.publishMonitoringLog(
          "SQL script execution error: " + e.getMessage(), NexlaMonitoringLogSeverity.ERROR);
      throw e;
    } finally {
      rollbackConnection();
    }
  }

  @SneakyThrows
  private Optional<List<Map<String, String>>> executeLineByLine(Reader reader, AtomicInteger upd) {
    StringBuilder command = new StringBuilder();
    // take only last SELECT output
    Optional<List<Map<String, String>>> lastResult = Optional.empty();
    BufferedReader lineReader = new BufferedReader(reader);
    String line;
    while ((line = lineReader.readLine()) != null) {
      long start = System.currentTimeMillis();
      LOGGER.info("[{}] Start executing SQL script line: {}", resource, line);
      insightsLogsPublisher.publishMonitoringLog(
          "Start executing SQL script line: " + line, NexlaMonitoringLogSeverity.INFO);
      Optional<List<Map<String, String>>> runResult = handleLine(command, line, upd);
      if (runResult.isPresent()) {
        lastResult = runResult;
      }
      long delay = System.currentTimeMillis() - start;
      String delayStr = InsightsLogsPublisher.formatDelayParts(delay);
      LOGGER.info("[{}] SQL script line executed (in {}): {}", resource, delayStr, line);
      insightsLogsPublisher.publishMonitoringLog(
          "SQL script line executed (in " + delayStr + "): " + line,
          NexlaMonitoringLogSeverity.INFO);
    }
    commitConnection();
    checkForMissingLineTerminator(command);
    return lastResult;
  }

  /**
   * @deprecated Since 3.5.4, this method is deprecated. Please close the {@link Connection} outside
   *     of this class.
   */
  @Deprecated
  public void closeConnection() {
    try {
      connection.close();
    } catch (Exception e) {
      // ignore
    }
  }

  private void setAutoCommit() {
    try {
      if (autoCommit != connection.getAutoCommit()) {
        connection.setAutoCommit(autoCommit);
      }
    } catch (SQLFeatureNotSupportedException e) {
      // Some drivers (e.g., Databricks JDBC driver) don't support disabling autoCommit
      LOGGER.warn(
          "Driver does not support setting autoCommit to {}. Continuing with driver's default"
              + " behavior.",
          autoCommit);
    } catch (Throwable t) {
      throw new RuntimeException("Could not set AutoCommit to " + autoCommit + ". Cause: " + t, t);
    }
  }

  private void commitConnection() {
    try {
      JdbcUtils.commitIfNeeded(connection);
    } catch (Throwable t) {
      throw new RuntimeException("Could not commit transaction. Cause: " + t, t);
    }
  }

  private void rollbackConnection() {
    try {
      JdbcUtils.rollbackIfNeeded(connection);
    } catch (Throwable t) {
      // ignore
    }
  }

  private void checkForMissingLineTerminator(StringBuilder command) {
    if (command != null && !command.toString().trim().isEmpty()) {
      throw new RuntimeException(
          "Line missing end-of-line terminator (" + delimiter + ") => " + command);
    }
  }

  private Optional<List<Map<String, String>>> handleLine(
      StringBuilder command, String line, AtomicInteger updateCnt) throws SQLException {
    String trimmedLine = line.trim();
    if (lineIsComment(trimmedLine)) {
      Matcher matcher = DELIMITER_PATTERN.matcher(trimmedLine);
      if (matcher.find()) {
        delimiter = matcher.group(5);
      }
    } else if (commandReadyToExecute(trimmedLine)) {
      command.append(line, 0, line.lastIndexOf(delimiter));
      command.append(LINE_SEPARATOR);
      Optional<List<Map<String, String>>> result = executeStatement(command.toString(), updateCnt);
      command.setLength(0);
      return result;
    } else if (!trimmedLine.isEmpty()) {
      command.append(line);
      command.append(LINE_SEPARATOR);
    }
    return Optional.empty();
  }

  private boolean lineIsComment(String trimmedLine) {
    return trimmedLine.startsWith("//") || trimmedLine.startsWith("--");
  }

  private boolean commandReadyToExecute(String trimmedLine) {
    // issue #561 remove anything after the delimiter
    return !fullLineDelimiter && trimmedLine.contains(delimiter)
        || fullLineDelimiter && trimmedLine.equals(delimiter);
  }

  private Optional<List<Map<String, String>>> executeStatement(
      String command, AtomicInteger updatedCount) throws SQLException {
    Statement statement = connection.createStatement();
    List<Map<String, String>> result = Lists.newArrayList();
    try {
      statement.setEscapeProcessing(escapeProcessing);
      String sql = command;
      if (removeCRs) {
        sql = sql.replace("\r\n", "\n");
      }
      boolean hasResults = statement.execute(sql);
      int updateCount = statement.getUpdateCount();
      if (updateCount != -1) {
        updatedCount.addAndGet(updateCount);
      }
      while (catchResults && hasResults) {
        checkWarnings(statement);
        result.addAll(catchResults(statement, hasResults));
        hasResults = statement.getMoreResults();
      }
    } finally {
      try {
        statement.close();
      } catch (Exception ignored) {
        // Ignore to workaround a bug in some connection pools
        // (Does anyone know the details of the bug?)
      }
    }
    return Optional.of(result).filter(x -> !x.isEmpty());
  }

  private void checkWarnings(Statement statement) throws SQLException {
    if (!throwWarning) {
      return;
    }
    // In Oracle, CREATE PROCEDURE, FUNCTION, etc. returns warning
    // instead of throwing exception if there is compilation error.
    SQLWarning warning = statement.getWarnings();
    if (warning != null) {
      throw warning;
    }
  }

  private List<Map<String, String>> catchResults(Statement statement, boolean hasResults) {
    if (!hasResults) {
      return Collections.emptyList();
    }
    try (ResultSet rs = statement.getResultSet()) {
      ResultSetMetaData md = rs.getMetaData();
      int cols = md.getColumnCount();
      List<String> columnNames = Lists.newArrayList();
      for (int i = 0; i < cols; i++) {
        String name = md.getColumnLabel(i + 1);
        columnNames.add(name);
      }
      List<Map<String, String>> results = Lists.newArrayList();
      while (rs.next()) {
        List<String> values = Lists.newArrayList();
        for (int i = 0; i < cols; i++) {
          String value = rs.getString(i + 1);
          values.add(value);
        }
        results.add(toLinkedHashMap(zip(columnNames, values)));
      }
      return results;
    } catch (SQLException e) {
      LOGGER.error("Error printing results: {}", e.getMessage());
      return Collections.emptyList();
    }
  }
}
