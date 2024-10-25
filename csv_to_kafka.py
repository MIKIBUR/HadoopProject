from kafka import KafkaProducer
import time
import logging
import pandas as pd

# Configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name
csv_file_path = '/data/data3.csv'  # Path to the CSV file inside the container

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_kafka_producer():
    attempts = 0
    max_attempts = 120  # Maximum number of connection attempts
    while attempts < max_attempts:
        try:
            producer = KafkaProducer(bootstrap_servers=kafka_broker)
            logger.info("Kafka producer initialized successfully")
            return producer
        except Exception as e:
            attempts += 1
            logger.warning(f"Failed to initialize Kafka producer. Attempt {attempts}/{max_attempts}. Error: {e}")
            time.sleep(1)  # Wait for 1 second before retrying
    logger.error("Failed to initialize Kafka producer after multiple attempts. Exiting.")
    raise Exception("Failed to initialize Kafka producer after multiple attempts")

def load_csv_to_kafka(file_path, producer, topic_name, batch_size=500, delay=1):
    chunk_size = 5000  # Read CSV in chunks of 5000 rows
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        batch = []
        for _, row in chunk.iterrows():
            message = ','.join(row.astype(str))
            batch.append(message.encode('utf-8'))

            if len(batch) >= batch_size:
                # Send batch to Kafka
                for msg in batch:
                    producer.send(topic_name, msg)
                producer.flush()
                logger.info(f'Sent {len(batch)} messages as a batch')
                batch.clear()  # Clear the batch
                time.sleep(delay)  # Delay between sending batches

        # Send any remaining messages in the batch
        if batch:
            for msg in batch:
                producer.send(topic_name, msg)
            producer.flush()
            logger.info(f'Sent {len(batch)} remaining messages as a batch')

if __name__ == "__main__":
    producer = initialize_kafka_producer()
    load_csv_to_kafka(csv_file_path, producer, topic_name)
    producer.close()