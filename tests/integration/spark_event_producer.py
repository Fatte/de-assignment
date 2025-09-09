from kafka import KafkaProducer
import json
import time
import yaml

def load_config():
    with open("../config/producer_config.yml", "r") as f:
        return yaml.safe_load(f)["producer_config"]["kafka"]
    
config = load_config()
topic = config["topic"]
bootstrap_servers = config["bootstrap_servers"]

producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

events = [
    ("device_id_1", {"timestamp": 1700000000, "temperature": 22.0, "event_duration": 2.3, "status": "ok"}),
    ("device_id_1", {"timestamp": 1700000020, "temperature": 23.0, "event_duration": 8.1, "status": "ok"}),
    ("device_id_2", {"timestamp": 1700000000, "temperature": 25.0, "event_duration": 5.5, "status": "ok"}),
    ("device_id_2", {"timestamp": 1700000020, "temperature": 30.0, "event_duration": 2.0, "status": "error"}),
    ("device_id_3", {"timestamp": 1700000020, "temperature": 30.0, "event_duration": 1.9, "status": "error"})
]

for event in events:
    producer.send(topic, key=event[0].encode("utf-8"), value=event[1])
    producer.flush()
    time.sleep(0.1)
