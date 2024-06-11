from kafka import KafkaConsumer
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, unix_timestamp, from_unixtime
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from datetime import datetime
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Kafka configuration
kafka_broker = 'kafka:29092'  # Kafka broker address inside the container
topic_name = 'test-topic'      # Kafka topic name
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentiment_model = SentimentIntensityAnalyzer()

# Initialize Spark session
spark = SparkSession.builder.appName("KafkaSparkMLlib").getOrCreate()

def classify_sentiment(compound_score):
    if compound_score >= 0.05:
        return 'pos'
    elif compound_score > -0.05:
        return 'neu'
    else:
        return 'neg'
    
def parse_message(message):
    timestamp_str, tweet, politician = message.split(',')
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
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
    
    train_data = []
    
    # Consume messages for the first second
    for i , message in enumerate(consumer):
        message_value = message.value.decode('utf-8')
        
        train_data.append(parse_message(message_value))
        if(i > 500):
            break
    # Stop consuming
    consumer.close()

    if not train_data:
        print("No data collected for training")
        return

    # Create a DataFrame from the collected training data
    df = spark.createDataFrame(train_data, ["timestamp", "tweet", "politician","rating","sentiment"])

    df = df.dropna()
    df.show()
    
    

if __name__ == "__main__":
    consume_from_kafka_and_train_model()

    # Stop Spark session
    spark.stop()
