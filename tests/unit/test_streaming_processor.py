import pytest
from pyspark.sql.types import StructType
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
import streaming_processor


@patch("streaming_processor.SparkSession")
def test_get_spark_session(mock_spark_session):
    mock_builder = MagicMock()
    mock_spark_session.builder = mock_builder
    mock_builder.master.return_value = mock_builder
    mock_builder.appName.return_value = mock_builder
    mock_builder.config.return_value = mock_builder
    mock_builder.getOrCreate.return_value = MagicMock()

    spark = streaming_processor.get_spark_session("TestApp")
    assert spark is not None


def test_get_event_schema():
    schema = streaming_processor.get_event_schema()
    assert isinstance(schema, StructType)
    field_names = [field.name for field in schema.fields]
    assert "timestamp" in field_names
    assert "temperature" in field_names
    assert "status" in field_names


@patch("streaming_processor.SparkSession")
def test_read_kafka_stream(mock_spark_session):
    mock_df = MagicMock()
    mock_reader = MagicMock()
    mock_reader.format.return_value = mock_reader
    mock_reader.option.return_value = mock_reader
    mock_reader.load.return_value = mock_df
    mock_spark_session.readStream = mock_reader

    result = streaming_processor.read_kafka_stream(mock_spark_session, "test_topic")
    assert result == mock_df


def test_write_stream():
    # Crea un mock del DataFrame
    mock_df = MagicMock()

    # Crea una catena di mock per il writer
    mock_writer = MagicMock()
    mock_df.writeStream.outputMode.return_value = mock_writer
    mock_writer.format.return_value = mock_writer
    mock_writer.option.return_value = mock_writer
    mock_writer.partitionBy.return_value = mock_writer
    mock_writer.trigger.return_value = mock_writer
    mock_writer.start.return_value = "stream_started"

    # Esegui la funzione
    from streaming_processor import write_stream
    result = write_stream(mock_df, "test-bucket")

    # Verifica
    assert result == "stream_started"


