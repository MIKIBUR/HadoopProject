#!/bin/bash

# Start Kafka in the background
/etc/confluent/docker/run &

# Wait for Kafka broker to be available
while ! nc -z localhost 9092; do
  sleep 0.1
done

# Create the Kafka topic
kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Wait for the Kafka process to end
wait -n
