import subprocess
import time
import yaml
from kafka import KafkaConsumer

def load_config():
    with open("../config/producer_config.yml", "r") as f:
        return yaml.safe_load(f)["producer_config"]["kafka"]

def test_producer_consumer():
    config = load_config()
    topic = config["topic"]
    bootstrap_servers = config["bootstrap_servers"]

    print("Avvio del producer...")
    producer_process = subprocess.Popen(
        ["python", "event_producer.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("Attesa per l'invio dei messaggi...")
    time.sleep(5)

 
    # Verifica se il processo è ancora attivo
    if producer_process.poll() is not None:
        print("Il producer è terminato prematuramente.")
        stdout, stderr = producer_process.communicate()
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        assert False, "Il producer è terminato prematuramente."


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
    producer_process.wait(timeout=5)

    stdout, stderr = producer_process.communicate(timeout=5)
    print("STDOUT del producer:")
    print(stdout)
    print("STDERR del producer:")
    print(stderr)

    print(f"Numero di messaggi ricevuti: {len(messages)}")
    assert len(messages) >= 1, "Nessun messaggio ricevuto dal producer"
