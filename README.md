# Hadoop, Spark and Kafka Data Analysis Project

This repository contains a Dockerized application for performing data analysis using Hadoop, Spark and Kafka.

## Prerequisites

- Docker Desktop (Windows)
- Docker Engine (Unix)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Installing

1. **Clone the repository:**

    ```sh
    git clone https://github.com/MIKIBUR/HadoopProject.git
    ```

2. **Build and run the Docker containers:**

    Use Docker Compose to build and start the containers in detached mode:

    ```sh
    docker-compose up -d --build
    ```

## Usage

Once the containers are up and running (some components may take some time to do so), you can interact with the enviorment.

### Running Spark Jobs

You can run Spark jobs by submitting them to the Spark cluster. For example:

```sh
docker exec -it spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /kafka_stream_output.py
```
