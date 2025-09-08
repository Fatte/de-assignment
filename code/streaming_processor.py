import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, date_format, window, avg, count, from_unixtime
from pyspark.sql.types import StructType, StringType, FloatType

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")

is_localstack = ENDPOINT_URL and ENDPOINT_URL.startswith("http://localhost")

# Costruisci configurazione S3 dinamica
s3_conf = {
    "spark.hadoop.fs.s3a.access.key": AWS_ACCESS_KEY_ID,
    "spark.hadoop.fs.s3a.secret.key": AWS_SECRET_ACCESS_KEY,
    "spark.hadoop.fs.s3a.endpoint": ENDPOINT_URL if is_localstack else f"s3.{AWS_DEFAULT_REGION}.amazonaws.com",
    "spark.hadoop.fs.s3a.path.style.access": "true" if is_localstack else "false",
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
}

# 1. Spark session
builder = SparkSession.builder \
    .appName("DeviceEventStreaming")
for k, v in s3_conf.items():
    builder = builder.config(k, v)
spark = builder.getOrCreate()

spark.sparkContext.setLogLevel("WARN")


# Debug: stampa configurazione
# print("=== CONFIGURAZIONE S3 ===")
# for k, v in s3_conf.items():
#     print(f"{k}: {v}")
# print("=========================")


# 2. Schema del payload JSON
event_schema = StructType() \
    .add("timestamp", FloatType()) \
    .add("temperature", FloatType()) \
    .add("status", StringType())

# 3. Lettura da Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "device_topic") \
    .option("startingOffsets", "latest") \
    .load()

# 4. Parsing e filtering
parsed_df = kafka_df \
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
    .withColumn("json", from_json(col("value"), event_schema)) \
    .select(
        col("key").alias("device_id"),
        from_unixtime(col("json.timestamp")).cast("timestamp").alias("event_time"),
        col("json.temperature").alias("temperature"),
        col("json.status").alias("status")
    ) \
    .filter(col("temperature").isNotNull()) \
    .filter(col("status") != 'error')

# 5. Aggregazione: media temperatura per device per minuto
aggregated_df = parsed_df \
    .withWatermark("event_time", "1 minute") \
    .groupBy(
        window(col("event_time"), "1 minute"),
        col("device_id")
    ) \
    .agg(
        avg("temperature").alias("avg_temperature"),
         count("event_time").alias("num_events")
    ) \
    .withColumn("window_start", date_format(col("window").getField("start"), "yyyy-MM-dd HH_mm"))

# 6. Output su console
output_path = f"s3a://{BUCKET_NAME}/stream_output/"
checkpoint_path = f"s3a://{BUCKET_NAME}/stream_checkpoints/"

query = aggregated_df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", output_path) \
    .option("checkpointLocation", checkpoint_path) \
    .partitionBy("window_start", "device_id") \
    .trigger(processingTime="60 seconds") \
    .start()


query.awaitTermination()
