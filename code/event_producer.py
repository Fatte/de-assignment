import yaml
import json
import time
from kafka import KafkaProducer
import random

# Simulated IoT data generator
def generate_event(schema, num_generators):
    event = {}
    for field in schema["event_schema"]["fields"]:
        name = field["name"]
        type_ = field["type"]

        if type_ == "datetime":
            event[name] = time.time()
        elif type_ == "float":
            event[name] = round(random.uniform(20.0, 30.0), 2)
        elif type_ == "enum":
            event[name] = random.choice(field["values"])
    key_name = schema["event_schema"]["key"]["name"]
    event_key = f"{key_name}_{random.randint(1, num_generators)}"
    return event, event_key


# Wait for Kafka service
time.sleep(20)

# Carica lo schema
with open("../config/event_schema.yml", "r") as f:
    schema = yaml.safe_load(f)

# Carica il producer config
with open("../config/producer_config.yml", "r") as f:
    producer_config = yaml.safe_load(f)["producer_config"]["kafka"]


# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=producer_config["bootstrap_servers"],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=producer_config["acks"],
    retries=producer_config["retries"],
    enable_idempotence=True if producer_config["delivery_exactly_once"] is True else False
)

# Send data every {{event_frequency}} seconds
topic = producer_config["topic"]
print(f"Producing messages to topic '{topic}'...")
while True:
    event, event_key = generate_event(schema, producer_config["num_generators"])
    producer.send(topic, key=event_key.encode("utf-8"), value=event)
    producer.flush()
    print(f"Sent: {event}")
    time.sleep(producer_config["event_frequency"])
