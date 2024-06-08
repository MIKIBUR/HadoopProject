from pyspark import SparkConf, SparkContext

if __name__ == "__main__":
    conf = SparkConf().setAppName("WordCount").setMaster("spark://spark-master:7077")
    sc = SparkContext(conf=conf)
    
    text_file = sc.textFile("hdfs://namenode:8020/data/lorem.txt")
    counts = text_file.flatMap(lambda line: line.split(" ")) \
                      .map(lambda word: (word, 1)) \
                      .reduceByKey(lambda a, b: a + b)
    
    counts.saveAsTextFile("hdfs://namenode:8020/output")
    sc.stop()


