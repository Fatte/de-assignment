
.PHONY: venv producer s3 bucket generate_env generate_aws_env processor percentile_job validate grafana test clean kill_producer kill_processor run

CONFIG_FILE=config/streaming_config.yml
ENV_FILE=.env.generated
ENV_FILE_AWS=s3/.env

venv:
	@test -d src/venv || python3 -m venv src/venv
	@src/venv/bin/pip install --upgrade pip
	@src/venv/bin/pip install -r requirements.txt

producer:
	cd "kafka" && \
	docker compose up -d && \
	echo "Waiting for Kafka setup..." && \
	sleep 20 && \
	cd "../src" && \
	bash -c 'nohup venv/bin/python event_producer.py > producer.log 2>&1 & disown'
	
s3:
	cd "s3" && \
	docker compose up -d
	
bucket:
	cd "s3" && \
	./create_bucket.sh
	
generate_env:
	@echo "Generating environment variables from YAML config..."
	@echo "KAFKA_BOOTSTRAP_SERVERS=$$(yq '.streaming_config.kafka.KAFKA_BOOTSTRAP_SERVERS' $(CONFIG_FILE))" > $(ENV_FILE)
	@echo "KAFKA_TOPIC_NAME=$$(yq '.streaming_config.kafka.KAFKA_TOPIC_NAME' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "STREAMING_AGGREGATED_S3_OUTPUT_PATH=$$(yq '.streaming_config.s3.STREAMING_AGGREGATED_S3_OUTPUT_PATH' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "STREAMING_AGGREGATED_S3_CHECKPOINT_PATH=$$(yq '.streaming_config.s3.STREAMING_AGGREGATED_S3_CHECKPOINT_PATH' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "STREAMING_RAW_S3_OUTPUT_PATH=$$(yq '.streaming_config.s3.STREAMING_RAW_S3_OUTPUT_PATH' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "STREAMING_RAW_S3_CHECKPOINT_PATH=$$(yq '.streaming_config.s3.STREAMING_RAW_S3_CHECKPOINT_PATH' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "PERCENTILE_VALIDATION_CSV_OUTPUT_PATH=$$(yq '.streaming_config.s3.PERCENTILE_VALIDATION_CSV_OUTPUT_PATH' $(CONFIG_FILE))" >> $(ENV_FILE)
	@echo "NUM_EVENT_THRESHOLD=$$(yq '.streaming_config.s3.NUM_EVENT_THRESHOLD' $(CONFIG_FILE))" >> $(ENV_FILE)

generate_aws_env:
	@echo "Generating environment variables for AWS connector..."
	@echo "Remember to change them before running the project!"
	@echo "AWS_ACCESS_KEY_ID=test" > $(ENV_FILE_AWS)
	@echo "AWS_SECRET_ACCESS_KEY=test" >> $(ENV_FILE_AWS)
	@echo "AWS_DEFAULT_REGION=eu-central-1" >> $(ENV_FILE_AWS)
	@echo "BUCKET_NAME=my-parametric-bucket" >> $(ENV_FILE_AWS)
	@echo "ENDPOINT_URL=s3.eu-central-1.amazonaws.com" >> $(ENV_FILE_AWS)
	@echo "PROFILE=default" >> $(ENV_FILE_AWS)

processor:
	@export $(shell grep -v '^#' s3/.env | xargs); \
	bash -c ' \
		set -a; \
        source $(ENV_FILE); \
        set +a; \
		nohup spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.sql.streaming.metricsEnabled=true \
		--conf spark.metrics.conf=src/metrics.properties \
		--conf spark.driver.extraJavaOptions="-javaagent:src/lib/jmx_prometheus_javaagent-1.4.0.jar=7071:src/lib/jmx_config.yaml" \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
        --conf spark.executorEnv.KAFKA_BOOTSTRAP_SERVERS=$$KAFKA_BOOTSTRAP_SERVERS \
		--conf spark.executorEnv.KAFKA_TOPIC_NAME=$$KAFKA_TOPIC_NAME \
		--conf spark.executorEnv.STREAMING_AGGREGATED_S3_OUTPUT_PATH=$$STREAMING_AGGREGATED_S3_OUTPUT_PATH \
		--conf spark.executorEnv.STREAMING_AGGREGATED_S3_CHECKPOINT_PATH=$$STREAMING_AGGREGATED_S3_CHECKPOINT_PATH \
        src/streaming_processor.py > streaming_processor.log 2>&1 & disown' && \
	bash -c ' \
		set -a; \
        source $(ENV_FILE); \
        set +a; \
		nohup spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.metrics.conf=src/metrics.properties \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
		--conf spark.executorEnv.KAFKA_BOOTSTRAP_SERVERS=$$KAFKA_BOOTSTRAP_SERVERS \
		--conf spark.executorEnv.KAFKA_TOPIC_NAME=$$KAFKA_TOPIC_NAME \
		--conf spark.executorEnv.STREAMING_RAW_S3_OUTPUT_PATH=$$STREAMING_RAW_S3_OUTPUT_PATH \
		--conf spark.executorEnv.STREAMING_RAW_S3_CHECKPOINT_PATH=$$STREAMING_RAW_S3_CHECKPOINT_PATH \
        src/streaming_raw_writer.py > streaming_raw_writer.log 2>&1 & disown'
		
percentile_job:
	@export $(shell grep -v '^#' s3/.env | xargs); \
	bash -c ' \
		set -a; \
        source $(ENV_FILE); \
        set +a; \
		nohup spark-submit \
		--packages org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.metrics.conf=src/metrics.properties \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
		--conf spark.executorEnv.STREAMING_RAW_S3_OUTPUT_PATH=$$STREAMING_RAW_S3_OUTPUT_PATH \
		--conf spark.executorEnv.PERCENTILE_VALIDATION_CSV_OUTPUT_PATH=$$PERCENTILE_VALIDATION_CSV_OUTPUT_PATH \
		--conf spark.executorEnv.NUM_EVENT_THRESHOLD=$$NUM_EVENT_THRESHOLD \
        src/percentile_processor.py > percentile_processor.log 2>&1 & disown'

validate:
	@export $(shell grep -v '^#' s3/.env | xargs); \
	bash -c ' \
		set -a; \
        source $(ENV_FILE); \
        set +a; \
		spark-submit \
		--packages org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.metrics.conf=src/metrics.properties \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
		--conf spark.executorEnv.STREAMING_AGGREGATED_S3_OUTPUT_PATH=$$STREAMING_AGGREGATED_S3_OUTPUT_PATH \
        src/schema_validator.py'
		
grafana:
	cd "grafana" && \
	docker compose up -d
	
test:
	cd "tests" && \
	bash -c '../src/venv/bin/python -m pytest --cov=../src unit/ '

clean:
	cd "kafka" && \
	docker compose down --volumes --remove-orphans && \
	docker container prune && \
	cd "../s3" && \
	docker compose down --volumes --remove-orphans && \
	docker container prune && \
	cd "../grafana" && \
	docker compose down --volumes --remove-orphans && \
	docker container prune
	
kill_producer:
	@PID=$$(ps aux | grep '[p]ython.*event_producer.py' | awk '{print $$2}'); \
	if [ -n "$$PID" ]; then \
		echo "Killing event_producer.py process with PID $$PID"; \
		kill $$PID; \
	else \
		echo "No event_producer.py process found."; \
	fi

kill_processor:
	@PID=$$(ps aux | grep '[p]ython.*streaming_processor.py' | awk '{print $$2}'); \
    if [ -n "$$PID" ]; then \
        echo "Killing streaming_processor.py process with PID $$PID"; \
        kill $$PID; \
    else \
        echo "No streaming_processor.py process found."; \
    fi; \
    PID2=$$(ps aux | grep '[p]ython.*streaming_raw_writer.py' | awk '{print $$2}'); \
    if [ -n "$$PID2" ]; then \
        echo "Killing streaming_raw_writer.py process with PID $$PID2"; \
        kill $$PID2; \
    else \
        echo "No streaming_raw_writer.py process found."; \
    fi

run:
	@echo "Running project..."
	sudo apt update && sudo apt install -y yq
	$(MAKE) venv
	$(MAKE) bucket
	$(MAKE) generate_env
	$(MAKE) producer
	$(MAKE) grafana
	$(MAKE) processor



