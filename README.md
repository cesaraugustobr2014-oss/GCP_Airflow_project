# Customer Experience Data Pipeline

End-to-End Data Engineering Pipeline using Apache Airflow, Spark, Google Cloud Storage, and BigQuery

## Overview

This project demonstrates a production-grade **Customer Experience Data Pipeline** built for analyzing customer reviews across multiple sources (Google Reviews, TripAdvisor, Yelp, Email, Social Media).

The pipeline implements a **3-layer data lake architecture** (RAW → TRUSTED → CURATED) with:

- ✅ **Data Ingestion** from CSV/JSON
- ✅ **Data Validation** and quality checks
- ✅ **Data Transformation** with PySpark
- ✅ **Sentiment Analysis** using VADER
- ✅ **Orchestration** with Apache Airflow
- ✅ **Data Warehouse** on BigQuery
- ✅ **Infrastructure as Code** with Terraform

---

## 🎯 Project Focus

**This is primarily a DATA ENGINEERING project, NOT a Machine Learning project.**

While sentiment analysis (VADER) is included, the core value is in demonstrating:

- 📦 **ETL/ELT processes** for large datasets
- 🧹 **Data cleaning and normalization**
- 🛡️ **Data quality enforcement**
- 🔄 **Pipeline orchestration**
- 📊 **Data warehouse modeling**
- ☁️ **Cloud architecture (GCP)**
- 🧪 **Testing and observability**

---

## 📊 Architecture

```
DATA SOURCES → INGESTION → RAW (GCS) → VALIDATION → TRANSFORMATION (Spark)
                                    ↓
                              TRUSTED (GCS) → SENTIMENT → CURATED (GCS)
                                    ↓
                              BIGQUERY → ANALYTICS & DASHBOARDS
```

### Data Lake Layers

| Layer | Description | Format |
|-------|-------------|--------|
| **RAW** | Original data (as-ingested) | Parquet (partitioned) |
| **TRUSTED** | Cleaned, validated data | Parquet (partitioned) |
| **CURATED** | Business-ready data | Parquet (partitioned) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | Apache Airflow |
| Processing | PySpark / Dataproc |
| Storage | Google Cloud Storage (Data Lake) |
| Warehouse | BigQuery |
| Sentiment | VADER (NLTK) |
| Data Quality | Custom checks |
| Infrastructure | Terraform |
| Containerization | Docker |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional, for Airflow)
- GCP account (optional, for cloud demo)

### Step 1: Setup Dependencies

```bash
cd /home/cesar/GCP_projects/customer-experience

# Install Python dependencies
make setup

# Or manually:
pip install -r requirements.txt
```

### Step 2: Generate Sample Data

```bash
# Generate 10,000 synthetic reviews
make generate-data

# Or run directly:
python scripts/generate_sample_data.py
```

### Step 3: Run Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Step 4: Run Airflow (Optional)

```bash
# Start Airflow with Docker Compose
make airflow-up

# Access UI at http://localhost:8080
# Username: airflow
# Password: airflow

# Stop when done
make airflow-down
```

---

## 📂 Project Structure

```
customer-experience-pipeline/
├── dags/                 # Apache Airflow DAGs
├── scripts/             # Utility scripts
├── ingestion/           # Data ingestion module
├── transformations/     # Data cleaning and sentiment
├── spark/               # PySpark jobs
├── data_quality/        # Data validation checks
├── sql/                 # SQL scripts (BigQuery)
├── data/                # Generated data (GITIGNORED)
│   ├── sample/         # Raw sample data
│   ├── raw/            # RAW layer (Parquet)
│   ├── trusted/        # TRUSTED layer (Parquet)
│   └── curated/        # CURATED layer (Parquet)
├── tests/               # Unit tests
├── terraform/           # Infrastructure as Code
├── docs/                # Documentation
├── docker-compose.yml   # Airflow configuration
├── Makefile             # Development commands
└── requirements.txt     # Python dependencies
```

---

## 📈 Pipeline Stages

1. **Data Generation** → Generate synthetic reviews with data quality issues
2. **Data Ingestion** → Read CSV, write to RAW layer (Parquet)
3. **Data Validation** → Schema, nulls, ranges, duplicates
4. **Data Transformation** → Clean, normalize, deduplicate (PySpark)
5. **Sentiment Analysis** → VADER classification (POSITIVE/NEUTRAL/NEGATIVE)
6. **Data Loading** → Create dimensions, load to BigQuery

---

## 🎨 Data Model

### BigQuery Schema

**Dataset:** `customer_experience`

| Table | Description |
|-------|-------------|
| `dim_source` | Source dimension (google_reviews, tripadvisor, etc.) |
| `dim_location` | Location dimension (city, state, country) |
| `fact_reviews` | Fact table with reviews and sentiment |

**Fact Table PARTITIONED BY:** `review_date`  
**Fact Table CLUSTERED BY:** `source_id, location_id, sentiment`

---

## ❓ Example Analytics Queries

```sql
-- 1. Count reviews by source
SELECT source, COUNT(*) as review_count
FROM customer_experience.fact_reviews
GROUP BY source
ORDER BY review_count DESC;

-- 2. Sentiment by city
SELECT city, sentiment, COUNT(*) as count
FROM customer_experience.fact_reviews
GROUP BY city, sentiment
ORDER BY city, count DESC;

-- 3. Negative sentiment percentage
SELECT 
  ROUND(SUM(CASE WHEN sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as negative_percentage
FROM customer_experience.fact_reviews;
```

See `sql/analytics.sql` for 10+ queries.

---

## 🧪 Data Quality

The synthetic dataset includes intentional issues to demonstrate data quality checks:

| Issue | Percentage | Description |
|-------|-----------|-------------|
| Duplicates | ~1% | Same review_id |
| Null text | ~0.5% | Missing review text |
| Invalid ratings | ~1% | Outside 1-5 range |
| Missing city | ~1% | City not provided |
| Inconsistent source case | ~1% | Mixed case in source names |

Run `make generate-data && python scripts/data_quality.py` to see all checks.

---

## ☁️ Google Cloud Integration

### Prerequisites

1. **Create GCP Project** and enable APIs:
   ```bash
   gcloud services enable storage.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

2. **Authenticate**:
   ```bash
   gcloud auth application-default login
   ```

3. **Configure** `.env`:
   ```bash
   cp .env.example .env
   # Edit .env with your GCP project details
   ```

4. **Provision Infrastructure** (Terraform):
   ```bash
   cd terraform
   terraform init
   terraform apply -var="project_id=YOUR_PROJECT_ID"
   ```

See `docs/gcp_setup.md` for detailed instructions.

---

## 📝 BigQuery Setup

### Create Dataset

```bash
bq --project_id=YOUR_PROJECT_ID mk --dataset customer_experience
```

### Create Tables

```bash
bq --project_id=YOUR_PROJECT_ID query --use_legacy_sql=false < sql/create_tables.sql
```

### Load Data

```bash
bq --project_id=YOUR_PROJECT_ID load \
  --source_format=PARQUET \
  customer_experience.reviews \
  gs://your-bucket/curated/customer_sentiment/*.parquet
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_ingestion.py -v

# Run with coverage
make test-coverage

# Run linting
make lint
```

---

## 🛠️ Development Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install dependencies |
| `make generate-data` | Generate sample data |
| `make test` | Run all tests |
| `make test-coverage` | Run tests with coverage |
| `make lint` | Run linting checks |
| `make format` | Format code with black |
| `make airflow-up` | Start Airflow with Docker |
| `make airflow-down` | Stop Airflow |
| `make clean` | Remove generated files |

---

## 📊 Cost Considerations

### Local Development
- **Cost:** $0 (runs on local machine)

### GCP Usage
- **Cloud Storage:** 5GB free tier
- **BigQuery:** 10GB querying free, 1TB storage free
- **Dataproc:** Pay-per-use, use ephemeral clusters

**Estimated Monthly Cost:**
- Development: $0
- Small production (daily, 10k records): <$5
- Medium production (hourly, 1M records): $20-50

See `docs/costs.md` for detailed breakdown.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `README.md` | This file |
| `docs/architecture.md` | Technical architecture |
| `docs/data_model.md` | Database schema |
| `docs/pipeline.md` | Pipeline details |
| `docs/structure.md` | Project structure |

---

## 🚢 Deployment

### AWS (Alternative)
- Replace GCS with **S3**
- Replace BigQuery with **Redshift** or **Athena**
- Use **MWAA** instead of Airflow

### Azure (Alternative)
- Replace GCS with **Azure Data Lake**
- Replace BigQuery with **Azure Synapse**
- Use **Azure Data Factory**

---

## 🎓 Lessons Learned

This project demonstrates:

1. **Data Engineering discipline** → Proper layering, validation, monitoring
2. **Scalability** → Spark-based processing handles millions of records
3. **Observability** → Clear metrics and logging throughout pipeline
4. **Reproducibility** → Seed fixed, deterministic data generation
5. **Production readiness** → IaC, tests, CI/CD, documentation

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

This is a portfolio project. Feel free to explore and use as reference.

---

## 📞 Contact

For questions or feedback, please open an issue on GitHub.
