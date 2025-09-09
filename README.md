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

---

## 📂 Project Structure

```bash
├── config
│   ├── event_schema.yml
│   ├── producer_config.yml
│   └── streaming_config.yml
├── src
│   ├── event_producer.py
│   ├── streaming_processor.py
│   ├── streaming_raw_writer.py
│   ├── percentile_processor.py
│   ├── lib
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
- **`streaming_config.yml`** → Contains parameters for the streaming processors (e.g., Kafka topic, S3 output paths, etc.). 

---

### `src/`
Core source code for streaming and batch processing:
- **`event_producer.py`** → Simulates IoT devices and sends events to Kafka.  
- **`streaming_processor.py`** → Processes events in real-time, applies transformations and aggregations.  
- **`streaming_raw_writer.py`** → Writes raw events to S3 in Parquet format.  
- **`percentile_processor.py`** → Batch job to compute percentiles over historical data.  
- **`lib`** → Contains Java agent and the confs used to expose Spark metrics to Prometheus.  
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

---

## 🚀 Runbook

### 1. Clone the repository
Download the project from GitHub and make sure your **Unix-based** machine satisfies the prerequisites described above.

```bash
git clone [<REPOSITORY_URL>](https://github.com/Fatte/de-assignment.git)
cd de-assignment
```

---

### 2. Generate the `.env` file
Create the `.env` file in the `s3` folder with:

```bash
make generate_aws_env
```

- The file contains environment variables (credentials, S3 connection settings, and bucket configuration).
- The generated file is just a **template with placeholder values** → you must update it with your actual credentials and configuration.

---

### 3. Configuration
Customize the parameters in the `config/` directory.  
- **Required**: `streaming_config.yml` → configure the S3 output paths.  

---

### 4. Run the end-to-end pipeline
Start the entire stack with:

```bash
make run
```

This command will sequentially:
- Create the Python **virtual environment**  
- Connect to **S3** and create the bucket (if it does not exist)  
- Set up **Kafka** (create topic + start the event producer)  
- Start **Grafana + Prometheus** at `http://localhost:3000` (username: admin - password: admin)
- Start **Spark Streaming jobs** at `http://localhost:4040`  

---

### 5. Run the batch job (95th percentile)
To run the Spark batch job that computes the 95th percentile:

```bash
make percentile_job
```

---

### 6. Run the tests
To execute the unit tests:

```bash
make test
```

---

## 📌 Command Cheat Sheet

| Command                | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `make generate_aws_env` | Generate `s3/.env` file with S3 credentials and bucket config (template values) |
| `make run`              | Launch full pipeline: S3 + Kafka + Spark streaming + Grafana/Prometheus      |
| `make percentile_job`   | Run Spark batch job to compute 95th percentile                               |
| `make clean`            | Destroy all the project docker containers                                    |
| `make kill producer`    | Kill the event producer script                                               |
| `make kill processor`   | Kill the streaming pyspark jobs                                              |

