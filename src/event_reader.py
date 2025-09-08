from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'device_topic',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # Legge dall'inizio del topic
    enable_auto_commit=True,
    group_id='my-group'
)

print("In ascolto su 'device_topic'...")
for message in consumer:
    print(f"Messaggio ricevuto: {message.value.decode('utf-8')}")
