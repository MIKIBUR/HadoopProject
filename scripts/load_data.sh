#!/bin/bash
hdfs dfs -mkdir /data
hdfs dfs -chmod 777 /data
hdfs dfs -copyFromLocal /data/lorem.txt /data
hdfs dfs -chmod 777 /
