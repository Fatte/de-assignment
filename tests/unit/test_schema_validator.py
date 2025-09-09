import pytest
from pyspark.sql.types import StructType
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
import schema_validator

@patch("schema_validator.SparkSession")
def test_get_spark_session(mock_spark_session):
    mock_builder = MagicMock()
    mock_spark_session.builder = mock_builder
    mock_builder.appName.return_value = mock_builder
    mock_builder.config.return_value = mock_builder
    mock_builder.getOrCreate.return_value = MagicMock()

    spark = schema_validator.get_spark_session("TestApp")
    assert spark is not None


def test_read_aggregated_stream():
    mock_spark = MagicMock()
    mock_df = MagicMock()
    mock_spark.read.parquet.return_value = mock_df

    path = "s3a://bucket/path"
    result_df = schema_validator.read_aggregated_stream(mock_spark, path)
    mock_spark.read.parquet.assert_called_once_with(path)

    assert result_df == mock_df


def test_validate_schema_success():
    mock_df = MagicMock()
    mock_df.columns = ['avg_temperature', 'avg_event_duration', 'num_events', 'device_id', 'window_start']
    mock_df.printSchema = MagicMock()
    mock_df.show = MagicMock()

    schema_validator.validate_schema(None, mock_df)
    mock_df.printSchema.assert_called_once()
    mock_df.show.assert_called_once_with(10, truncate=False)


def test_validate_schema_failure():
    mock_df = MagicMock()
    mock_df.columns = ['device_id', 'window_start']
    mock_df.printSchema = MagicMock()
    mock_df.show = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        schema_validator.validate_schema(None, mock_df)

    assert "Schema non valido" in str(exc_info.value)





