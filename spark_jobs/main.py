from kafka import KafkaConsumer
from pyspark.sql import SparkSession
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import re
from pyspark.sql.functions import col, lower, when, unix_timestamp, pandas_udf
import pandas as pd

# Kafka configuration
kafka_broker = 'kafka:29092'
topic_name = 'test-topic'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentiment_model = SentimentIntensityAnalyzer()

# UDF to identify the politician mentioned in the tweet

def find_politician(tweet):
    if not tweet:  # Handle empty or null tweets
        return None

    politicians = {
        "trump": ["trump", "donald"],
        "clinton": ["clinton", "hillary"],  
        "obama": ["obama", "barack"],
        "sanders": ["sanders", "bernie"]
    }

    # Dictionary to store occurrences and positions
    occurrences = {}

    for politician, names in politicians.items():
        total_count = 0
        positions = []  # List to store the positions of the first match of each name

        # Count all occurrences for each name related to the politician
        for name in names:
            matches = list(re.finditer(rf'{name}', tweet, re.IGNORECASE))
            total_count += len(matches)

            # Only add the position of the first match if there are any matches
            if matches:
                positions.append(matches[0].start())

        if total_count > 0 and positions:
            # Save total count and the earliest position of the first match
            occurrences[politician] = {
                "count": total_count,
                "first_position": min(positions)  # Get the earliest position from all names
            }

    if not occurrences:
        return None  # No politician found

    # Sort by count (descending) and then by first position (ascending)
    sorted_politicians = sorted(
        occurrences.items(),
        key=lambda x: (-x[1]["count"], x[1]["first_position"])
    )

    # Return the politician with the highest priority
    return sorted_politicians[0][0]



# Initialize Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkMLlib") \
    .getOrCreate()

# Spark UDFs
@pandas_udf(FloatType())
def get_rating_pandas_udf(texts: pd.Series) -> pd.Series:
    return texts.apply(lambda text: sentiment_model.polarity_scores(text)["compound"])

@pandas_udf(StringType())
def find_politician_pandas_udf(tweets: pd.Series) -> pd.Series:
    def find_politician(tweet):
        if not tweet:
            return None

        politicians = {
            "trump": ["trump", "donald"],
            "clinton": ["clinton", "hillary"],
            "obama": ["obama", "barack"],
            "sanders": ["sanders", "bernie"]
        }

        occurrences = {}
        for politician, names in politicians.items():
            total_count = 0
            positions = []

            for name in names:
                matches = list(re.finditer(rf'{name}', tweet, re.IGNORECASE))
                total_count += len(matches)
                if matches:
                    positions.append(matches[0].start())

            if total_count > 0 and positions:
                occurrences[politician] = {
                    "count": total_count,
                    "first_position": min(positions)
                }

        if not occurrences:
            return None

        sorted_politicians = sorted(
            occurrences.items(),
            key=lambda x: (-x[1]["count"], x[1]["first_position"])
        )

        return sorted_politicians[0][0]

    return tweets.apply(find_politician)


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
        StructField("given_politician", StringType(), True)
    ])

    batch = []
    for message in consumer:
        message_value = message.value.decode('utf-8')
        batch.append(tuple(message_value.split(',')))

        if len(batch) >= batch_size:
            # Create a DataFrame from the batch
            df = spark.createDataFrame(batch, schema=schema)

            # Apply transformations to add necessary columns
            df = df.withColumn("timestamp", unix_timestamp(df["timestamp_str"], "yyyy-MM-dd HH:mm:ss"))
            df = df.withColumn("rating", get_rating_pandas_udf(df["tweet"]))
            df = df.withColumn("politician", find_politician_pandas_udf(df["tweet"]))
            df = df.withColumn("is_correct_politician",when(lower(col("given_politician")) == lower(col("politician")), True).otherwise(False))
            df = df.drop("timestamp_str")

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
