from kafka import KafkaConsumer
from pyspark.sql import SparkSession
from datetime import datetime
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pyspark.sql.types import StructType, StructField, StringType, FloatType
from pyspark.sql.functions import udf
from pyspark.sql import functions as F
import time

# Kafka configuration
kafka_broker = 'kafka:29092'
topic_name = 'test-topic'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentiment_model = SentimentIntensityAnalyzer()

# Initialize Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkMLlib") \
    .getOrCreate()

# Spark UDFs to classify sentiment and parse the timestamp
get_rating_udf = udf(lambda text: sentiment_model.polarity_scores(text)["compound"], FloatType())
parse_timestamp_udf = udf(lambda ts: int(time.mktime(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').timetuple())), StringType())

def consume_from_kafka_and_train_model(batch_size=100):
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_broker,
        auto_offset_reset='earliest',
        group_id=None
    )

    schema = StructType([
        StructField("timestamp_str", StringType(), True),
        StructField("tweet", StringType(), True),
        StructField("politician", StringType(), True)
    ])

    batch = []
    for message in consumer:
        message_value = message.value.decode('utf-8')
        batch.append(tuple(message_value.split(',')))

        if len(batch) >= batch_size:
            # Create a DataFrame from the batch
            df = spark.createDataFrame(batch, schema=schema)

            # Apply transformations to add only necessary columns
            df = df.withColumn("timestamp", parse_timestamp_udf(df["timestamp_str"])) \
                   .withColumn("rating", get_rating_udf(df["tweet"])) \
                   .drop("timestamp_str")  # Drop the original timestamp column

            # Write batch to the database
            df.write \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://postgres:5432/spark_db") \
                .option("dbtable", "politicians") \
                .option("user", "spark_user") \
                .option("password", "spark_password") \
                .mode("append") \
                .save()
            
            logger.info(f"Processed and saved {len(batch)} messages.")
            batch.clear()  # Clear the batch for the next set of messages

    # Stop consuming after loop ends
    consumer.close()


if __name__ == "__main__":
    consume_from_kafka_and_train_model(batch_size=100)
    spark.stop()
