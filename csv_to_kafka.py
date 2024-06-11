import csv
from kafka import KafkaProducer
import time
import logging

# Configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name
csv_file_path = '/data/data2.csv'  # Path to the CSV file inside the container

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

def load_csv_to_kafka(file_path, producer):
    while True:
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            i = 0
            batch_size = 500  # Number of rows to send as a batch
            for row in reader:
                message = ','.join(row)
                if i < batch_size:
                    producer.send(topic_name, message.encode('utf-8'))
                    i += 1
                    producer.flush()
                    if i == batch_size:
                        logger.info(f'Sent {batch_size} messages as a batch')
                else:
                    producer.send(topic_name, message.encode('utf-8'))
                    producer.flush()
                    logger.info(f'Sent message: {message}')
                    time.sleep(1)  # Introduce a delay of 1 second between each message
            logger.info("Reached end of file.")

if __name__ == "__main__":
    producer = initialize_kafka_producer()
    load_csv_to_kafka(csv_file_path, producer)
    producer.close()