import subprocess
import time
import yaml
from kafka import KafkaConsumer

# Carica il producer config
with open("config/producer_config.yml", "r") as f:
    producer_config = yaml.safe_load(f)["producer_config"]["kafka"]

TOPIC = producer_config["topic"]
BOOTSTRAP_SERVERS = producer_config["bootstrap_servers"]

def test_producer_consumer():

    # Avvia il producer in background
    producer_process = subprocess.Popen(
        ["python", "code/event_producer.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Aspetta che il producer inizi a inviare
    time.sleep(5)

    # Avvia il consumer
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        consumer_timeout_ms=10000
    )

    messages = []
    for msg in consumer:
        messages.append(msg.value)
        print(f"Ricevuto: {msg.value}")
        if len(messages) >= 1:
            break

    # Termina il producer
    producer_process.terminate()

    assert len(messages) >= 1, "Nessun messaggio ricevuto dal producer"

