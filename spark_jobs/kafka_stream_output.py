from kafka import KafkaConsumer

# Configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name

def consume_from_kafka():
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_broker,
        auto_offset_reset='earliest',  # Start reading from the earliest offset
        group_id=None  # Disable consumer groups
    )

    for message in consumer:
        print(f"Received message: {message.value.decode('utf-8')}")

if __name__ == "__main__":
    consume_from_kafka()
