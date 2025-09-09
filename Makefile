
.PHONY: producer s3 bucket processor grafana test clean kill_producer kill_processor

producer:
	cd "kafka" && \
	docker compose up -d && \
	cd "../src" && \
	bash -c 'nohup venv/bin/python event_producer.py > producer.log 2>&1 & disown'
	
s3:
	cd "s3" && \
	docker compose up -d
	
bucket:
	cd "s3" && \
	./create_bucket.sh

processor:
	@export $(shell grep -v '^#' s3/.env | xargs); \
	bash -c 'nohup spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.sql.streaming.metricsEnabled=true \
		--conf spark.metrics.conf=src/metrics.properties \
		--conf spark.driver.extraJavaOptions="-javaagent:src/jmx_prometheus_javaagent-1.4.0.jar=7071:src/config.yaml" \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.AWS_DEFAULT_REGION=$$AWS_DEFAULT_REGION \
        --conf spark.executorEnv.BUCKET_NAME=$$BUCKET_NAME \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
        --conf spark.executorEnv.PROFILE=$$PROFILE \
        src/streaming_processor.py > streaming_processor.log 2>&1 & disown' && \
	bash -c 'nohup spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.metrics.conf=src/metrics.properties \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.AWS_DEFAULT_REGION=$$AWS_DEFAULT_REGION \
        --conf spark.executorEnv.BUCKET_NAME=$$BUCKET_NAME \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
        --conf spark.executorEnv.PROFILE=$$PROFILE \
        src/streaming_raw_writer.py > streaming_raw_writer.log 2>&1 & disown'
		
percentile_job:
	@export $(shell grep -v '^#' s3/.env | xargs); \
	bash -c 'nohup spark-submit \
		--packages org.apache.hadoop:hadoop-aws:3.3.2 \
		--conf spark.metrics.conf=src/metrics.properties \
        --conf spark.executorEnv.AWS_ACCESS_KEY_ID=$$AWS_ACCESS_KEY_ID \
        --conf spark.executorEnv.AWS_SECRET_ACCESS_KEY=$$AWS_SECRET_ACCESS_KEY \
        --conf spark.executorEnv.AWS_DEFAULT_REGION=$$AWS_DEFAULT_REGION \
        --conf spark.executorEnv.BUCKET_NAME=$$BUCKET_NAME \
        --conf spark.executorEnv.ENDPOINT_URL=$$ENDPOINT_URL \
        --conf spark.executorEnv.PROFILE=$$PROFILE \
        src/percentile_processor.py > percentile_processor.log 2>&1 & disown'
		
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

