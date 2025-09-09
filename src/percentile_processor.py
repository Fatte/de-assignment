import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date, col, avg, stddev, countDistinct, expr


def get_spark_session(app_name="DeviceEventPercentileProcessor"):
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

def read_raw_stream(spark, path):
    return spark.read.parquet(path)

def add_event_date(df):
    return df.withColumn("date", to_date(col("event_time")))

def compute_stats(df, threshold):
    stats_df = df.groupBy("device_id", "date").agg(
        countDistinct("*").alias("num_events"),
        avg("event_duration").alias("avg_event_duration"),
        stddev("event_duration").alias("stddev_event_duration")
    )
    return stats_df.filter(col("num_events") > threshold).select(
        "device_id", "date", "avg_event_duration", "stddev_event_duration"
    )

def filter_outliers(df, stats_df):
    enriched_df = df.join(stats_df, on=["device_id", "date"], how="inner")
    return enriched_df.filter(
        col("event_duration") > col("avg_event_duration") - 3 * col("stddev_event_duration")
    ).filter(
        col("event_duration") < col("avg_event_duration") + 3 * col("stddev_event_duration")
    )

def compute_percentile(df):
    return df.groupBy("device_id", "date").agg(
        expr("percentile_approx(event_duration, 0.95)").alias("event_duration_p95")
    )

def write_to_csv(df, path):
    df.write.option("header", True).mode("overwrite").csv(path)


if __name__ == "__main__":
    STREAMING_RAW_S3_OUTPUT_PATH = os.environ.get("STREAMING_RAW_S3_OUTPUT_PATH")
    PERCENTILE_VALIDATION_CSV_OUTPUT_PATH = os.environ.get("PERCENTILE_VALIDATION_CSV_OUTPUT_PATH")
    NUM_EVENT_THRESHOLD = int(os.environ.get("NUM_EVENT_THRESHOLD"))

    spark = get_spark_session()
    raw_df = read_raw_stream(spark, STREAMING_RAW_S3_OUTPUT_PATH)
    dated_df = add_event_date(raw_df)
    stats_df = compute_stats(dated_df, NUM_EVENT_THRESHOLD)
    filtered_df = filter_outliers(dated_df, stats_df)
    percentile_df = compute_percentile(filtered_df)
    write_to_csv(percentile_df, PERCENTILE_VALIDATION_CSV_OUTPUT_PATH)

