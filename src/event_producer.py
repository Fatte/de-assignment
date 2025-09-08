import yaml
import json
import time
from kafka import KafkaProducer
import random


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


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def initialize_producer(producer_config):
    print("Initializing KafkaProducer...")
    return KafkaProducer(
        bootstrap_servers=producer_config["bootstrap_servers"],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks=producer_config["acks"],
        retries=producer_config["retries"],
        enable_idempotence=True if producer_config["delivery_exactly_once"] is True else False
    )


def produce_events(producer, schema, producer_config, test=False):
    topic = producer_config["topic"]
    print(f"Producing messages to topic '{topic}'...")
    test_loop_count = 30
    while (not test) or (test_loop_count > 0):
        event, event_key = generate_event(schema, producer_config["num_generators"])
        producer.send(topic, key=event_key.encode("utf-8"), value=event)
        producer.flush()
        print(f"Sent: {event}")
        time.sleep(producer_config["event_frequency"])
        if test:
            test_loop_count -= 1
        

if __name__ == "__main__":
    # Wait for Kafka service
    time.sleep(20)

    # Load event schema
    schema = load_yaml("../config/event_schema.yml")

    # Load producer config
    producer_config = load_yaml("../config/producer_config.yml")["producer_config"]["kafka"]

    # Create the KafkaProducer
    producer = initialize_producer(producer_config)

    # Produce and Send the events
    produce_events(producer, schema, producer_config, test=False)