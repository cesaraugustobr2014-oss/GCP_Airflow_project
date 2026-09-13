# Project Structure

```
customer-experience-pipeline/
│
├── README.md                    # Main README
├── Makefile                     # Development commands
├── requirements.txt             # Python dependencies
├── requirements-test.txt        # Testing dependencies
├── docker-compose.yml           # Airflow Docker configuration
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── pytest.ini                   # Pytest configuration
│
├── dags/                        # Apache Airflow DAGs
│   ├── __init__.py
│   ├── customer_reviews_local_pipeline.py    # Local pipeline DAG
│   └── customer_reviews_gcp_pipeline.py      # GCP pipeline DAG
│
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   └── generate_sample_data.py  # Sample data generator
│
├── ingestion/                   # Data ingestion module
│   ├── __init__.py
│   └── ingest_reviews.py        # CSV to Parquet ingestion
│
├── transformations/             # Data transformations
│   ├── __init__.py
│   ├── clean_reviews.py         # Data cleaning
│   └── sentiment_analysis.py    # VADER sentiment analysis
│
├── spark/                       # Spark processing jobs
│   ├── __init__.py
│   ├── transform_reviews.py     # PySpark transformation job
│   └── utils.py                 # Spark session utilities
│
├── data_quality/                # Data quality checks
│   ├── __init__.py
│   └── checks.py                # Validation functions
│
├── sql/                         # SQL scripts
│   ├── create_dataset.sql       # BigQuery dataset creation
│   ├── create_tables.sql        # Table DDL
│   ├── data_quality.sql         # Quality check queries
│   └── analytics.sql            # Business analytics queries
│
├── data/                        # Data directory (GITIGNORED)
│   ├── sample/                  # Generated sample data
│   ├── raw/                     # RAW layer (Parquet)
│   ├── trusted/                 # TRUSTED layer (Parquet)
│   └── curated/                 # CURATED layer (Parquet)
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_ingestion.py        # Ingestion tests
│   ├── test_transformations.py  # Transformation tests
│   ├── test_sentiment.py        # Sentiment analysis tests
│   ├── test_data_quality.py     # Data quality tests
│   └── test_spark.py            # Spark job tests
│
├── terraform/                   # Infrastructure as Code
│   ├── main.tf                  # Terraform config
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output variables
│   ├── storage.tf               # GCS buckets
│   ├── bigquery.tf              # BigQuery resources
│   └── README.md                # Terraform docs
│
├── docs/                        # Project documentation
│   ├── architecture.md
│   ├── data_model.md
│   ├── pipeline.md
│   └── images/
│
└── .github/                     # GitHub workflows
    └── workflows/
        └── tests.yml            # CI/CD pipeline
```

## Directory Purposes

| Directory | Purpose |
|-----------|---------|
| `dags/` | Airflow DAG definitions |
| `scripts/` | Standalone Python scripts |
| `ingestion/` | Data ingestion module |
| `transformations/` | Data cleaning and transformation |
| `spark/` | PySpark jobs |
| `data_quality/` | Data validation checks |
| `sql/` | SQL scripts for BigQuery |
| `data/` | Generated data files |
| `tests/` | Unit tests |
| `terraform/` | GCP infrastructure code |
| `docs/` | Documentation |

## Data Layers

| Layer | Description | Format |
|-------|-------------|--------|
| **sample/** | Generated sample data | CSV |
| **raw/** | Input data (as-is) | Parquet (partitioned) |
| **trusted/** | Cleaned data | Parquet (partitioned) |
| **curated/** | Business-ready data | Parquet |

## Environment Variables

See `.env.example` for full list.

Key variables:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: GCP region (default: us-central1)
- `GCS_RAW_BUCKET`: RAW layer bucket name
- `BIGQUERY_DATASET`: BigQuery dataset ID
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON
