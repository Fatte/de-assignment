import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, from_json, date_format, window, avg, count, from_unixtime
from pyspark.sql.types import StructType, StringType, FloatType

def get_spark_session(app_name="DeviceEventStreaming") -> SparkSession:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    ENDPOINT_URL = os.environ.get("ENDPOINT_URL")

    is_localstack = ENDPOINT_URL and ENDPOINT_URL.startswith("http://localhost")

    s3_conf = {
        "spark.hadoop.fs.s3a.access.key": AWS_ACCESS_KEY_ID,
        "spark.hadoop.fs.s3a.secret.key": AWS_SECRET_ACCESS_KEY,
        "spark.hadoop.fs.s3a.endpoint": ENDPOINT_URL if is_localstack else f"s3.{AWS_DEFAULT_REGION}.amazonaws.com",
        "spark.hadoop.fs.s3a.path.style.access": "true" if is_localstack else "false",
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
        .add("status", StringType())

def read_kafka_stream(spark: SparkSession, topic: str) -> DataFrame:
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .load()

def parse_and_filter(df: DataFrame, schema: StructType) -> DataFrame:
    return df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
        .withColumn("json", from_json(col("value"), schema)) \
        .select(
            col("key").alias("device_id"),
            from_unixtime(col("json.timestamp")).cast("timestamp").alias("event_time"),
            col("json.temperature").alias("temperature"),
            col("json.status").alias("status")
        ) \
        .filter(col("temperature").isNotNull()) \
        .filter(col("status") != 'error')

def aggregate_events(df: DataFrame) -> DataFrame:
    return df.withWatermark("event_time", "1 minute") \
        .groupBy(
            window(col("event_time"), "1 minute"),
            col("device_id")
        ) \
        .agg(
            avg("temperature").alias("avg_temperature"),
            count("event_time").alias("num_events")
        ) \
        .withColumn("window_start", date_format(col("window").getField("start"), "yyyy-MM-dd HH_mm"))

def write_stream(df: DataFrame, bucket_name: str):
    output_path = f"s3a://{bucket_name}/stream_output/"
    checkpoint_path = f"s3a://{bucket_name}/stream_checkpoints/"
    return df.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", output_path) \
        .option("checkpointLocation", checkpoint_path) \
        .partitionBy("window_start", "device_id") \
        .trigger(processingTime="60 seconds") \
        .start()

if __name__ == "__main__":
    spark = get_spark_session()
    schema = get_event_schema()
    kafka_df = read_kafka_stream(spark, topic="device_topic")
    parsed_df = parse_and_filter(kafka_df, schema)
    aggregated_df = aggregate_events(parsed_df)
    query = write_stream(aggregated_df, os.environ.get("BUCKET_NAME"))
    query.awaitTermination()