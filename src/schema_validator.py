import os
from pyspark.sql import SparkSession


def get_spark_session(app_name="AggregatedDataSchemaValidator"):
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


def read_aggregated_stream(spark, path):
    df = spark.read.parquet(path)
    print("✅ Parquet letto correttamente da S3.")
    return df


def validate_schema(spark, aggregated_df):
    aggregated_df.printSchema()

    expected_fields = {'avg_temperature', 'avg_event_duration', 'num_events', 'device_id', 'window_start'}
    actual_fields = set(aggregated_df.columns)

    if expected_fields.issubset(actual_fields):
        print("✅ Schema valido. Mostro un sample...")
        aggregated_df.show(10, truncate=False)
    else:
        missing = expected_fields - actual_fields
        print(f"❌ Schema non valido. Campi mancanti: {missing}")
        raise ValueError(f"❌ Schema non valido. Campi mancanti: {missing}")


if __name__ == "__main__":
    STREAMING_AGGREGATED_S3_OUTPUT_PATH = os.environ.get("STREAMING_AGGREGATED_S3_OUTPUT_PATH")
    spark = get_spark_session()
    aggregated_df = read_aggregated_stream(spark, STREAMING_AGGREGATED_S3_OUTPUT_PATH)
    validate_schema(spark, aggregated_df)
    

