import pytest
import yaml
import json
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
import event_producer


def test_generate_event_structure():
    schema = {
        "event_schema": {
            "fields": [
                {"name": "timestamp", "type": "datetime"},
                {"name": "temperature", "type": "float"},
                {"name": "status", "type": "enum", "values": ["ok", "fail"]}
            ],
            "key": {"name": "device_id"}
        }
    }
    event, key = event_producer.generate_event(schema, 3)
    assert "timestamp" in event
    assert "temperature" in event
    assert "status" in event
    assert key.startswith("device_id_")


def test_load_yaml(tmp_path):
    test_file = tmp_path / "test.yml"
    test_file.write_text("key: value")
    result = event_producer.load_yaml(str(test_file))
    assert result == {"key": "value"}


@patch("event_producer.KafkaProducer")
def test_initialize_producer(mock_kafka):
    config = {
        "bootstrap_servers": "localhost:9092",
        "acks": "all",
        "retries": 3,
        "delivery_exactly_once": True
    }
    producer = event_producer.initialize_producer(config)
    mock_kafka.assert_called_once()
    assert producer == mock_kafka.return_value


@patch("event_producer.time.sleep", return_value=None)
def test_produce_events_test_mode(mock_sleep):
    mock_producer = MagicMock()
    schema = {
        "event_schema": {
            "fields": [
                {"name": "timestamp", "type": "datetime"},
                {"name": "temperature", "type": "float"},
                {"name": "status", "type": "enum", "values": ["ok", "fail"]}
            ],
            "key": {"name": "device_id"}
        }
    }
    config = {
        "topic": "test-topic",
        "num_generators": 2,
        "event_frequency": 0.01
    }

    # Run in test mode (30 iterations)
    event_producer.produce_events(mock_producer, schema, config, test=True)
    assert mock_producer.send.call_count == 30
    assert mock_producer.flush.call_count == 30
