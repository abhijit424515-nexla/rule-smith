package com.nexla.connector.sql.poll.strategy;

import static com.nexla.connector.properties.SqlConfigAccessor.OFFSET_POSITION_TIMESTAMP;
import static com.nexla.connector.properties.SqlConfigAccessor.PARTITION_KEY;
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonMap;

import com.nexla.admin.client.NexlaSchema;
import com.nexla.connect.common.SourceRecordCreator;
import com.nexla.connector.sql.poll.Range;
import com.nexla.connector.sql.poll.timestamp.TimestampConstants;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Stream;
import lombok.extern.slf4j.Slf4j;
import one.util.streamex.StreamEx;
import org.javatuples.Pair;

/**
 * Stateless processor for timestamp column mode.
 *
 * <p>Handles reading records ordered by a timestamp column and tracking the last processed value.
 * This processor implements the same logic as the original JdbcSourceTask's timestamp mode
 * handling.
 *
 * <p>The {@link #process(ProcessingContext)} method is equivalent to the original inline timestamp
 * mode code path in JdbcSourceTask.doCollectRecords():
 *
 * <ol>
 *   <li>Calculate next range via {@link #getNextRangeTimestamp} (same time-based range calculation)
 *   <li>Set internal config bounds (internalTimestampColumnFrom/To)
 *   <li>Read stream via StreamReader adapter (same probe service call path)
 *   <li>Create records with timestamp-based offsets (same OFFSET_POSITION_TIMESTAMP key)
 *   <li>Track max timestamp value across batch
 * </ol>
 *
 * <h3>Usage</h3>
 *
 * <p>Used by both SingleTableProcessor and MultiTableProcessor facades. The facades configure the
 * ProcessingContext differently:
 *
 * <ul>
 *   <li>SingleTableProcessor: Fixed ranges from config props
 *   <li>MultiTableProcessor: Dynamic ranges from actual DB max or current time
 * </ul>
 *
 * @see SingleTableProcessor
 * @see MultiTableProcessor
 * @see IncrementingModeProcessor
 */
@Slf4j
public final class TimestampModeProcessor implements ModeProcessor {

  /** Singleton instance for production use. */
  public static final TimestampModeProcessor INSTANCE = new TimestampModeProcessor();

  /** Package-private constructor for testing. */
  TimestampModeProcessor() {}

  /**
   * Process timestamp mode using context state.
   *
   * @param ctx processing context with configured ranges and offsets
   * @return pair of source records and optional schema
   * @throws IOException if stream reading fails
   */
  @Override
  public Pair<List<SourceRecordCreator>, Optional<NexlaSchema>> process(final ProcessingContext ctx)
      throws IOException {

    final Optional<Range<Long>> rangeOpt = getNextRangeTimestamp(ctx);

    if (!rangeOpt.isPresent()) {
      return Pair.with(emptyList(), Optional.empty());
    }

    final Range<Long> range = rangeOpt.get();

    ctx.getConfig().internalTimestampColumnFrom = range.getFrom();
    ctx.getConfig().internalTimestampColumnTo = range.getTo();

    log.info("Reading table/query={}", ctx.getTableName());
    log.info(
        "processTimestampMode query parameters: table={}, internalTimestampColumnFrom={}, "
            + "internalTimestampColumnTo={}, timestampColumn={}, supportsFractional={}",
        ctx.getTableName(),
        ctx.getConfig().internalTimestampColumnFrom,
        ctx.getConfig().internalTimestampColumnTo,
        ctx.getCurrentTimestampColumnName(),
        ctx.isSupportsFractional());

    final Pair<StreamEx<LinkedHashMap<String, Object>>, Optional<NexlaSchema>> result =
        ctx.getStreamReader()
            .readStream(
                ctx.getConfig(),
                Optional.ofNullable(ctx.getCurrentIncrementingColumnName()),
                Optional.ofNullable(ctx.getCurrentTimestampColumnName()),
                Optional.ofNullable(ctx.getCurrentPerTableMode()),
                Optional.ofNullable(ctx.getCurrentPerTableFilter()));

    try (Stream<LinkedHashMap<String, Object>> dataStream = result.getValue0()) {
      final AtomicLong lastTsValue = new AtomicLong(-1);
      final AtomicLong indexCounter = new AtomicLong(0);
      final String timestampColumn = ctx.getCurrentTimestampColumnName();

      final List<SourceRecordCreator> records =
          StreamEx.of(dataStream.iterator())
              .map(
                  dataMap -> {
                    final long timestampValue = getTimestampValue(dataMap, timestampColumn);
                    lastTsValue.set(timestampValue);
                    final Map<String, Object> sourceOffset =
                        singletonMap(OFFSET_POSITION_TIMESTAMP, timestampValue + "");
                    final Map<String, String> partition =
                        singletonMap(PARTITION_KEY, ctx.getTableName());
                    return ctx.getRecordCreator()
                        .create(
                            dataMap,
                            partition,
                            sourceOffset,
                            indexCounter.getAndIncrement(),
                            rangeOpt,
                            Optional.of(timestampValue));
                  })
              .toList();

      ctx.updateMetricName(range.getFrom(), lastTsValue.get());

      if (!records.isEmpty()) {
        ctx.setLastProcessedTimestamp(lastTsValue.get());
      }
      return Pair.with(records, result.getValue1());
    }
  }

  /**
   * Calculate next range to process by timestamp column.
   *
   * @param ctx processing context
   * @return optional range for next batch
   */
  public static Optional<Range<Long>> getNextRangeTimestamp(final ProcessingContext ctx) {
    final int increment = ctx.isSupportsFractional() ? 1 : 1000;
    final Long fromTs = ctx.getFromTimestamp();
    final Long toTs = ctx.getToTimestamp();
    final Long lastProcessedTimestamp = ctx.getLastProcessedTimestamp();

    Range<Long> result = null;
    if (lastProcessedTimestamp == null) {
      result = new Range<>(fromTs, toTs);
    } else if (lastProcessedTimestamp < toTs) {
      final long nextFrom = lastProcessedTimestamp + increment;
      result = new Range<>(nextFrom, toTs);
    }

    if ((result == null) || (result.getFrom() > result.getTo())) {
      return Optional.empty();
    } else {
      return Optional.of(result);
    }
  }

  /**
   * Extract timestamp value from a data record.
   *
   * @param dataMap the data record
   * @param timestampColumn the timestamp column name
   * @return timestamp value in milliseconds
   */
  public static long getTimestampValue(
      final LinkedHashMap<String, Object> dataMap, final String timestampColumn) {
    final Object o = dataMap.get(timestampColumn);
    if (o instanceof Date) {
      return ((Date) o).getTime();
    } else {
      final Pair<Boolean, String> unsupportedSDFFormat =
          TimestampConstants.isUnsupportedSDFFormat(o);

      if (unsupportedSDFFormat.getValue0()) {
        final DateTimeFormatter formatter =
            DateTimeFormatter.ofPattern(unsupportedSDFFormat.getValue1());
        return LocalDateTime.parse(o.toString(), formatter)
            .atZone(ZoneOffset.UTC)
            .toInstant()
            .toEpochMilli();
      }

      for (final SimpleDateFormat sdf : TimestampConstants.TIMESTAMP_DATE_FORMATS) {
        try {
          return sdf.parse(o.toString()).getTime();
        } catch (Exception ignored) {
          // Try next format
        }
      }
    }
    throw new IllegalStateException("Could not parse " + o);
  }

  /**
   * Check if there is more data to process.
   *
   * @param ctx processing context
   * @return true if more data may be available
   */
  @Override
  public boolean hasMoreData(final ProcessingContext ctx) {
    final Long toTs = ctx.getToTimestamp();
    final Long lastProcessedTimestamp = ctx.getLastProcessedTimestamp();

    if (toTs == null) {
      return false;
    }

    return lastProcessedTimestamp == null || lastProcessedTimestamp < toTs;
  }
}
