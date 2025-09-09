import pytest
from pyspark.sql.types import StructType
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
import percentile_processor

@patch("percentile_processor.SparkSession")
def test_get_spark_session(mock_spark_session):
    mock_builder = MagicMock()
    mock_spark_session.builder = mock_builder
    mock_builder.appName.return_value = mock_builder
    mock_builder.config.return_value = mock_builder
    mock_builder.getOrCreate.return_value = MagicMock()

    spark = percentile_processor.get_spark_session("TestApp")
    assert spark is not None



@patch("percentile_processor.to_date")
@patch("percentile_processor.col")
def test_add_event_date(mock_col, mock_to_date):
    df = MagicMock()
    
    # Simula col("event_time") → mocked_column
    mock_col.return_value = "mocked_column"
    
    # Simula to_date(col("event_time")) → mocked_date_column
    mock_to_date.return_value = "mocked_date_column"
    
    # Simula df.withColumn("date", to_date(...)) → mocked_df
    df.withColumn.return_value = "mocked_df"

    result = percentile_processor.add_event_date(df)

    mock_col.assert_called_once_with("event_time")
    mock_to_date.assert_called_once_with("mocked_column")
    df.withColumn.assert_called_once_with("date", "mocked_date_column")
    assert result == "mocked_df"


@patch("percentile_processor.col")
@patch("percentile_processor.countDistinct")
@patch("percentile_processor.avg")
@patch("percentile_processor.stddev")
def test_compute_stats(mock_stddev, mock_avg, mock_count_distinct, mock_col):
    df = MagicMock()
    grouped = MagicMock()
    aggregated = MagicMock()
    filtered = MagicMock()
    selected = MagicMock()

    # Simula le funzioni Spark
    mock_count_distinct.return_value.alias.return_value = "num_events_col"
    mock_avg.return_value.alias.return_value = "avg_event_duration_col"
    mock_stddev.return_value.alias.return_value = "stddev_event_duration_col"

    # Simula col("num_events") > threshold
    mock_num_events_col = MagicMock()
    mock_num_events_col.__gt__.return_value = "num_events_gt_threshold"
    mock_col.return_value = mock_num_events_col

    df.groupBy.return_value = grouped
    grouped.agg.return_value = aggregated
    aggregated.filter.return_value = filtered
    filtered.select.return_value = selected

    result = percentile_processor.compute_stats(df, threshold=100)

    mock_count_distinct.assert_called_once_with("*")
    mock_avg.assert_called_once_with("event_duration")
    mock_stddev.assert_called_once_with("event_duration")
    mock_col.assert_called_once_with("num_events")
    mock_num_events_col.__gt__.assert_called_once_with(100)
    assert result == selected


@patch("percentile_processor.col")
def test_filter_outliers(mock_col):
    df = MagicMock()
    stats_df = MagicMock()
    enriched_df = MagicMock()
    filtered_1 = MagicMock()
    filtered_2 = MagicMock()

    # Mock delle colonne
    mock_event_duration_1 = MagicMock(name="event_duration_1")
    mock_avg_duration_1 = MagicMock(name="avg_event_duration_1")
    mock_stddev_duration_1 = MagicMock(name="stddev_event_duration_1")

    mock_event_duration_2 = MagicMock(name="event_duration_2")
    mock_avg_duration_2 = MagicMock(name="avg_event_duration_2")
    mock_stddev_duration_2 = MagicMock(name="stddev_event_duration_2")

    # Simula operazioni aritmetiche
    mock_stddev_duration_1.__rmul__.return_value = MagicMock(name="3stddev_1")
    mock_avg_duration_1.__sub__.return_value = MagicMock(name="avg_minus_3stddev_1")
    mock_event_duration_1.__gt__.return_value = MagicMock(name="gt_expr")

    mock_stddev_duration_2.__rmul__.return_value = MagicMock(name="3stddev_2")
    mock_avg_duration_2.__add__.return_value = MagicMock(name="avg_plus_3stddev_2")
    mock_event_duration_2.__lt__.return_value = MagicMock(name="lt_expr")

    mock_col.side_effect = [
        mock_event_duration_1,
        mock_avg_duration_1,
        mock_stddev_duration_1,
        mock_event_duration_2,
        mock_avg_duration_2,
        mock_stddev_duration_2
    ]

    df.join.return_value = enriched_df
    enriched_df.filter.side_effect = [filtered_1]
    filtered_1.filter.return_value = filtered_2

    result = percentile_processor.filter_outliers(df, stats_df)

    assert result == filtered_2
    df.join.assert_called_once_with(stats_df, on=["device_id", "date"], how="inner")
    assert enriched_df.filter.call_count == 1
    assert filtered_1.filter.call_count == 1



@patch("percentile_processor.expr")
def test_compute_percentile(mock_expr):
    df = MagicMock()
    grouped = MagicMock()
    aggregated = MagicMock()
    mock_expr_result = MagicMock()

    df.groupBy.return_value = grouped
    grouped.agg.return_value = aggregated
    mock_expr.return_value = mock_expr_result
    mock_expr_result.alias.return_value = "aliased_expr"

    result = percentile_processor.compute_percentile(df)

    mock_expr.assert_called_once_with("percentile_approx(event_duration, 0.95)")
    mock_expr_result.alias.assert_called_once_with("event_duration_p95")
    grouped.agg.assert_called_once_with("aliased_expr")
    assert result == aggregated


def test_write_to_csv():
    df = MagicMock()
    writer = MagicMock()
    df.write = writer
    writer.option.return_value = writer
    writer.mode.return_value = writer
    writer.csv.return_value = None

    result = percentile_processor.write_to_csv(df, "mock_path")
    assert result is None



