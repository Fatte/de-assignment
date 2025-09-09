# DE Takehome Test: Event Streaming and Processing Pipeline

## Project Overview

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

---

## Project Structure

.
├── LICENSE
├── Makefile
├── README.md
├── config
│   ├── event_schema.yml
│   └── producer_config.yml
├── grafana
│   ├── dashboards
│   ├── docker-compose.yml
│   ├── prometheus
│   └── provisioning
├── kafka
│   └── docker-compose.yml
├── nohup.out
├── percentile_processor.log
├── requirements.txt
├── s3
│   ├── create_bucket.sh
│   ├── docker-compose.yml
│   └── volume
├── src
│   ├── __pycache__
│   ├── config.yaml
│   ├── event_producer.py
│   ├── jmx_prometheus_javaagent-1.4.0.jar
│   ├── metrics.properties
│   ├── percentile_processor.py
│   ├── producer.log
│   ├── streaming_processor.py
│   ├── streaming_raw_writer.py
│   └── venv
└── tests
    ├── integration
    └── unit

