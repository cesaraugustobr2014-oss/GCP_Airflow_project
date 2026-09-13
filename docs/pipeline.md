# Pipeline Documentation

## Overview

The customer reviews pipeline processes customer feedback from multiple sources, performs data validation and cleaning, calculates sentiment, and loads the results into a data warehouse for analytics.

## Pipeline Stages

### 1. Data Generation (Optional)

**Purpose:** Generate synthetic sample data for testing

**Script:** `scripts/generate_sample_data.py`

**Command:**
```bash
make generate-data
```

**Features:**
- Generates 10,000 reviews
- Includes intentional data quality issues for testing
- Uses seed 42 for reproducibility

**Output:** `data/sample/reviews.csv`

---

### 2. Data Ingestion

**Purpose:** Read reviews from CSV and write to RAW layer

**Module:** `ingestion.ingest_reviews`

**Tasks:**
- Read CSV file
- Add ingestion metadata
- Convert to Parquet format
- Write to RAW layer (partitioned)

**Output:** `data/raw/reviews/year=YYYY/month=MM/day=DD/*.parquet`

---

### 3. Data Validation

**Purpose:** Validate data quality before transformation

**Module:** `data_quality.checks`

**Checks:**
- Schema validation (required columns, types)
- Null checks (review_id, rating, text)
- Rating validation (1-5 range)
- Source validation (supported sources only)
- Duplicate detection (by review_id)
- Empty text detection

**Output:** Validation report with metrics

---

### 4. Data Transformation

**Purpose:** Clean and normalize data

**Module:** `transformations.clean_reviews`

**Transformations:**
- Text cleaning (strip whitespace, normalize spaces)
- Source normalization (lowercase, mapping)
- City/state/country normalization
- Rating validation and conversion
- Date validation and formatting
- Duplicate removal

**Output:** Cleaned data in TRUSTED layer

---

### 5. Sentiment Analysis

**Purpose:** Classify sentiment of customer reviews

**Module:** `transformations.sentiment_analysis`

**Method:** VADER (Valence Aware Dictionary for Sentiment Reasoning)

**Output:**
- `sentiment`: POSITIVE, NEUTRAL, or NEGATIVE
- `sentiment_score`: -1.0 to +1.0

**Formula:**
- POSITIVE: score ≥ 0.5
- NEUTRAL: -0.5 < score < 0.5
- NEGATIVE: score ≤ -0.5

**Output:** Curated dataset in CURATED layer

---

### 6. Data Loading

**Purpose:** Load data into BigQuery

**Steps:**
1. Load dimension tables (dim_source, dim_location)
2. Load fact table (fact_reviews)
3. Partition by review_date
4. Cluster by source_id, location_id, sentiment

**Tools:**
- BigQuery API
- Airflow Google Cloud Operators
- PySpark (optional for large datasets)

---

## Airflow DAG Structure

### Local Pipeline (`customer_reviews_local_pipeline.py`)

```
generate_or_detect_input
    ↓
ingest_reviews
    ↓
validate_raw_data
    ↓
transform_reviews
    ↓
calculate_sentiment
    ↓
run_data_quality_checks
```

### GCP Pipeline (`customer_reviews_gcp_pipeline.py`)

```
generate_or_detect_input
    ↓
upload_to_gcs_raw
    ↓
get_gcs_raw_bucket
    ↓
create_dataproc_cluster (optional)
    ↓
submit_pyspark_job
    ↓
load_to_bigquery
    ↓
run_bigquery_checks
```

## Task Dependencies

All tasks follow a sequential pattern:

1. Each task depends on the previous task completing successfully
2. Tasks can be re-run independently (idempotent)
3. Failures trigger retries (up to 3 times)

## Idempotency

All tasks are idempotent:
- Can be re-run multiple times without issues
- Use overwrite mode for file writing
- BigQuery uses WRITE_TRUNCATE for loads

## Error Handling

| Scenario | Action |
|----------|--------|
| Task failure | Retry up to 3 times with 5-minute delay |
| Validation failure | DAG fails immediately (fail-fast) |
| Data quality issues | Logged, optionally filtered out |
| Network timeout | Retry with exponential backoff |

## Monitoring

### Airflow UI
- DAG runs visible at `http://localhost:8080`
- Task logs accessible from UI
- DAG runs history tracked

### Logging
- All tasks log to stdout
- Airflow stores logs in `logs/` directory
- Failed task logs available in UI

### Metrics
- Record counts at each stage
- Validation failure counts
- Sentiment distribution
- Processing time

## Performance

### Local Processing
- 10,000 records: ~1-2 minutes
- Memory usage: ~500MB
- Disk usage: ~50MB (RAW) + ~25MB (TRUSTED) + ~25MB (CURATED)

### GCP Processing
- Can scale to millions of records
- Dataproc cluster auto-scales
- BigQuery handles large datasets efficiently

## Cost Optimization

### Local
- Free (runs on local machine)

### GCP
- Use ephemeral Dataproc clusters
- Shutdown clusters after job completion
- Use partitioning and clustering in BigQuery to reduce scan costs
- Enable BigQuery storage optimization

## Troubleshooting

### Common Issues

1. **File not found**
   - Ensure `make generate-data` was run
   - Check file paths in code

2. **Parquet write error**
   - Ensure sufficient disk space
   - Check directory permissions

3. **Validation failures**
   - Check data quality issues in sample data
   - Review validation rules in `data_quality/checks.py`

4. **Airflow DAG stuck**
   - Check Airflow logs: `docker compose logs -f`
   - Verify dependencies are installed: `pip install -r requirements.txt`

5. **Sentiment analysis timeout**
   - VADER is fast (< 1 second per 1000 records)
   - Check if dataset is too large for local memory

## Extensions

### Real-Time Processing
- Replace CSV input with Pub/Sub topic
- Use Dataflow for streaming

### Advanced Analytics
- Add BERT/RoBERTa for sentiment (requires more resources)
- Add topic modeling for issue extraction
- Add NER for entity recognition

### Deployment
- Use Cloud Composer for managed Airflow
- Use Cloud Build for CI/CD
- Use Artifact Registry for container images

## Best Practices

1. **Always validate input data** before processing
2. **Log all transformations** for audit trail
3. **Use partitioning** for large datasets
4. **Test locally** before deploying to GCP
5. **Monitor costs** when using GCP services
6. **Use IAM least privilege** for service accounts
7. **Never commit secrets** to Git
