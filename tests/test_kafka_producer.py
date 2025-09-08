import subprocess
import time
import yaml
from kafka import KafkaConsumer

def load_config():
    with open("config/producer_config.yml", "r") as f:
        return yaml.safe_load(f)["producer_config"]["kafka"]

def test_producer_consumer():
    config = load_config()
    topic = config["topic"]
    bootstrap_servers = config["bootstrap_servers"]

    print("Avvio del producer...")
    producer_process = subprocess.Popen(
        ["python", "code/event_producer.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("Attesa per l'invio dei messaggi...")
    time.sleep(5)

    stdout, stderr = producer_process.communicate(timeout=10)
    print(f"stdout: {stdout}")
    print(f"stderr: {stderr}")

    print("Avvio del consumer...")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        consumer_timeout_ms=10000
    )

    messages = []
    for msg in consumer:
        messages.append(msg.value)
        print(f"Messaggio ricevuto: {msg.value}")
        if len(messages) >= 1:
            break

    print("Terminazione del producer...")
    producer_process.terminate()

    print(f"Numero di messaggi ricevuti: {len(messages)}")
    assert len(messages) >= 1, "Nessun messaggio ricevuto dal producer"
