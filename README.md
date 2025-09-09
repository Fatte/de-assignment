# DE Takehome Test: Event Streaming and Processing Pipeline

## 📖 Project Overview

This project implements a complete event streaming and processing pipeline using:

- Apache Spark (Structured Streaming)
- Kafka (via Docker)
- S3 (real or simulated via LocalStack)
- Grafana+Prometheus (via Docker) for real-time monitoring
- GitHub Actions for CI
- A modular Makefile for orchestration

It includes:
- A Kafka-based event producer
- A Spark streaming processor and raw events writer
- A percentile computation job
- A Grafana dashboard for monitoring
- Unit tests

---

## ⚙️ Pre-requirements

Before running the project, ensure the following are installed on your **Unix-based machine**:

- ✅ Apache Spark **3.5.0 or higher**
- ✅ Docker (with Docker Compose)
- ✅ AWS CLI
- ✅ yq package (apt install yq) for handling yml file in bash

---

## 📂 Project Structure

```bash
├── config
│   ├── event_schema.yml
│   └── producer_config.yml
├── src
│   ├── event_producer.py
│   ├── streaming_processor.py
│   ├── streaming_raw_writer.py
│   ├── percentile_processor.py
│   ├── config.yaml
│   ├── jmx_prometheus_javaagent-1.4.0.jar
│   └── metrics.properties
├── kafka
│   └── docker-compose.yml
├── s3
│   ├── create_bucket.sh
│   └── docker-compose.yml
├── grafana
│   ├── dashboards
│   ├── docker-compose.yml
│   ├── prometheus
│   └── provisioning
├── tests
    ├── integration
    └── unit
├── Makefile
├── requirements.txt
├── README.md
└── LICENSE
```
### `config/`
Contains configuration files used by the producer and schema validation:
- **`event_schema.yml`** → Defines the expected structure of incoming IoT events.  
- **`producer_config.yml`** → Contains parameters for the event producer (e.g., Kafka topic, frequency, etc.).  

---

### `src/`
Core source code for streaming and batch processing:
- **`event_producer.py`** → Simulates IoT devices and sends events to Kafka.  
- **`streaming_processor.py`** → Processes events in real-time, applies transformations and aggregations.  
- **`streaming_raw_writer.py`** → Writes raw events to S3 in Parquet format.  
- **`percentile_processor.py`** → Batch job to compute percentiles over historical data.  
- **`config.yaml`** → Prometheus exporter configuration for Spark metrics.  
- **`jmx_prometheus_javaagent-1.4.0.jar`** → Java agent used to expose Spark metrics to Prometheus.  
- **`metrics.properties`** → Spark metrics configuration file.  

---

### `kafka/`
- **`docker-compose.yml`** → Docker Compose setup for Kafka and Zookeeper.  

---

### `s3/`
Docker Compose setup for LocalStack (S3 simulation) and bucket creation:
- **`create_bucket.sh`** → Script to create the S3 bucket used by Spark.  
- **`docker-compose.yml`** → Defines the LocalStack container.  

---

### `grafana/`
Monitoring stack configuration:
- **`dashboards/`** → Predefined Grafana dashboards.  
- **`prometheus/`** → Prometheus configuration files.  
- **`provisioning/`** → Grafana provisioning setup (data sources, dashboards).  
- **`docker-compose.yml`** → Starts Grafana and Prometheus containers.  

---

### `tests/`
Contains unit and integration tests:
- **`unit/`** → Unit tests for individual components.  
- **`integration/`** → Integration tests for end-to-end validation.  

---

### Root files
- **`Makefile`** → Orchestrates the entire pipeline: starting services, running Spark jobs, testing, and cleanup.  
- **`requirements.txt`** → Python dependencies for the producer and test scripts.  
- **`README.md`** → Project documentation.  
- **`LICENSE`** → License file for the project.
