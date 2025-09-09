import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, from_json, date_format, window, avg, count, from_unixtime
from pyspark.sql.types import StructType, StringType, FloatType


def get_spark_session(app_name="DeviceEventStreaming") -> SparkSession:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    ENDPOINT_URL = os.environ.get("ENDPOINT_URL")

    s3_conf = {
        "spark.hadoop.fs.s3a.access.key": AWS_ACCESS_KEY_ID,
        "spark.hadoop.fs.s3a.secret.key": AWS_SECRET_ACCESS_KEY,
        "spark.hadoop.fs.s3a.endpoint": ENDPOINT_URL,
        "spark.hadoop.fs.s3a.path.style.access": "true" if ENDPOINT_URL and ENDPOINT_URL.startswith("http://localhost") else "false",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    }

    builder = SparkSession.builder.appName(app_name)
    for k, v in s3_conf.items():
        builder = builder.config(k, v)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def get_event_schema() -> StructType:
    return StructType() \
        .add("timestamp", FloatType()) \
        .add("temperature", FloatType()) \
        .add("event_duration", FloatType()) \
        .add("status", StringType())

def read_kafka_stream(spark: SparkSession, topic: str, bootstrap_servers: str) -> DataFrame:
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .load()

def parse_and_filter(df: DataFrame, schema: StructType) -> DataFrame:
    return df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
        .withColumn("json", from_json(col("value"), schema)) \
        .select(
            col("key").alias("device_id"),
            from_unixtime(col("json.timestamp")).cast("timestamp").alias("event_time"),
            col("json.event_duration").alias("event_duration"),
            col("json.temperature").alias("temperature"),
            col("json.status").alias("status")
        ) \
        .filter(col("temperature").isNotNull()) \
        .filter(col("event_duration").isNotNull()) \
        .filter(col("status") != 'error')

def aggregate_events(df: DataFrame) -> DataFrame:
    return df.withWatermark("event_time", "1 minute") \
        .groupBy(
            window(col("event_time"), "1 minute"),
            col("device_id")
        ) \
        .agg(
            avg("temperature").alias("avg_temperature"),
            avg("event_duration").alias("avg_event_duration"),
            count("event_time").alias("num_events")
        ) \
        .withColumn("window_start", date_format(col("window").getField("start"), "yyyy-MM-dd HH_mm"))

def write_stream(df: DataFrame, output_path: str, checkpoint_path: str):
    return df.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", output_path) \
        .option("checkpointLocation", checkpoint_path) \
        .partitionBy("device_id", "window_start") \
        .trigger(processingTime="60 seconds") \
        .start()

if __name__ == "__main__":
    STREAMING_AGGREGATED_S3_OUTPUT_PATH = os.environ.get("STREAMING_AGGREGATED_S3_OUTPUT_PATH")
    STREAMING_AGGREGATED_S3_CHECKPOINT_PATH = os.environ.get("STREAMING_AGGREGATED_S3_CHECKPOINT_PATH")
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC_NAME = os.environ.get("KAFKA_TOPIC_NAME")

    print(STREAMING_AGGREGATED_S3_OUTPUT_PATH, STREAMING_AGGREGATED_S3_CHECKPOINT_PATH, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NAME)

    spark = get_spark_session()
    schema = get_event_schema()
    kafka_df = read_kafka_stream(spark, KAFKA_TOPIC_NAME, KAFKA_BOOTSTRAP_SERVERS)
    parsed_df = parse_and_filter(kafka_df, schema)
    aggregated_df = aggregate_events(parsed_df)
    query = write_stream(aggregated_df, STREAMING_AGGREGATED_S3_OUTPUT_PATH, STREAMING_AGGREGATED_S3_CHECKPOINT_PATH)
    query.awaitTermination()