from kafka import KafkaConsumer
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, unix_timestamp, from_unixtime
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from datetime import datetime
import time

# Kafka configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name

# Initialize Spark session
spark = SparkSession.builder.appName("KafkaSparkMLlib").getOrCreate()

def parse_message(message):
    # Assuming message format: "01/09/2019 07:15,371.94"
    timestamp_str, value_str = message.split(',')
    timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M')
    value = float(value_str)
    return timestamp, value

def consume_from_kafka_and_train_model():
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_broker,
        auto_offset_reset='earliest',  # Start reading from the earliest offset
        group_id=None  # Disable consumer groups
    )
    
    train_data = []
    start_time = datetime.now()
    
    # Consume messages for the first second
    for message in consumer:
        message_value = message.value.decode('utf-8')
        timestamp, value = parse_message(message_value)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        train_data.append((timestamp, value))
        
        if elapsed_time > 1:
            break

    # Stop consuming
    consumer.close()

    if not train_data:
        print("No data collected for training")
        return

    # Create a DataFrame from the collected training data
    df = spark.createDataFrame(train_data, ["timestamp", "value"])

    # Convert timestamp to Unix timestamp for easier handling
    df = df.withColumn("timestamp", unix_timestamp(col("timestamp")))

    # Create lagged features
    windowSpec = Window.orderBy("timestamp")
    df = df.withColumn("prev_value", lag("value", 1).over(windowSpec))
    df = df.withColumn("timestamp", from_unixtime(col("timestamp")))

    # Drop rows with null values (the first row will have a null previous value)
    df = df.dropna()
    df.show()
    
    

if __name__ == "__main__":
    consume_from_kafka_and_train_model()

    # Stop Spark session
    spark.stop()
