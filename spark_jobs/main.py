from kafka import KafkaConsumer
from pyspark.sql import SparkSession, Row
from datetime import datetime
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import time

# Kafka configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentiment_model = SentimentIntensityAnalyzer()

# Initialize Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkMLlib") \
    .getOrCreate()

def classify_sentiment(compound_score):
    if compound_score >= 0.05:
        return 'pos'
    elif compound_score > -0.05:
        return 'neu'
    else:
        return 'neg'
    
def parse_message(message):
    timestamp_str, tweet, politician = message.split(',')
    timestamp = int(time.mktime(datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timetuple()))
    rating = sentiment_model.polarity_scores(tweet)["compound"]
    sentiment = classify_sentiment(rating)
    return timestamp, tweet, politician, rating, sentiment

def consume_from_kafka_and_train_model():
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_broker,
        auto_offset_reset='earliest',  # Start reading from the earliest offset
        group_id=None  # Disable consumer groups
    )
    
    schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("tweet", StringType(), True),
    StructField("politician", StringType(), True),
    StructField("rating", FloatType(), True),
    StructField("sentiment", StringType(), True)
    ])

    # Consume messages for the first second
    for i , message in enumerate(consumer):
        message_value = message.value.decode('utf-8')
        
        row = Row((parse_message(message_value)))
        new_df = spark.createDataFrame(row, schema)
        new_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/spark_db") \
            .option("dbtable", "politicians") \
            .option("user", "spark_user") \
            .option("password", "spark_password") \
            .mode("append") \
            .save()
        # new_df.show()
        # logger.info("Iteration number: "+str(i))
        
        # if(i > 50):
        #     break
    # Stop consuming
    consumer.close()

if __name__ == "__main__":
    consume_from_kafka_and_train_model()

    # Stop Spark session
    spark.stop()
