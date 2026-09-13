#!/usr/bin/env python3
"""
Customer Reviews GCP Pipeline - Apache Airflow DAG.

This DAG extends the local pipeline to integrate with Google Cloud Platform:
- Read from Google Cloud Storage (GCS)
- Process data with PySpark on Dataproc (optional)
- Load results to BigQuery

Usage:
    This DAG requires GCP credentials and bucket configuration.
    Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use ADC.

Configuration:
    - GCS_RAW_BUCKET: Bucket for RAW layer
    - GCS_TRUSTED_BUCKET: Bucket for TRUSTED layer
    - GCS_CURATED_BUCKET: Bucket for CURATED layer
    - BIGQUERY_DATASET: BigQuery dataset ID
    - BIGQUERY_PROJECT: BigQuery project ID
"""

import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitPySparkJobOperator,
    DataprocDeleteClusterOperator,
)
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalToGoogleCloudStorageOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQuery

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
}

# DAG
dag = DAG(
    dag_id="customer_reviews_gcp_pipeline",
    default_args=default_args,
    description="GCP pipeline for processing customer reviews with Spark",
    schedule_interval="@daily",
    catchup=False,
)


# ============================================
# Task 1: Generate or Detect Input Data
# ============================================

def gen_or_detect_input_local(**context):
    """Generate sample data locally before uploading to GCS."""
    import subprocess
    from pathlib import Path
    
    script_path = Path(__file__).parent.parent / "scripts" / "generate_sample_data.py"
    output_path = Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"
    
    if not output_path.exists():
        subprocess.run(
            ["python3", str(script_path), "--num-records", "10000"],
            cwd=Path(__file__).parent.parent,
            check=True,
        )
    
    return str(output_path)


generate_input_gcp = PythonOperator(
    task_id="generate_or_detect_input",
    python_callable=gen_or_detect_input_local,
    dag=dag,
)


# ============================================
# Task 2: Upload to GCS RAW Layer
# ============================================

raw_bucket_name = os.environ.get("GCS_RAW_BUCKET", "customer-experience-raw")
trusted_bucket_name = os.environ.get("GCS_TRUSTED_BUCKET", "customer-experience-trusted")
gcp_project_id = os.environ.get("GCP_PROJECT_ID", "your-project-id")
gcp_region = os.environ.get("GCP_REGION", "us-central1")
bq_dataset = os.environ.get("BIGQUERY_DATASET", "customer_experience")

upload_to_gcs_raw = LocalToGoogleCloudStorageOperator(
    task_id="upload_to_gcs_raw",
    src=str(Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"),
    dst="reviews.csv",
    bucket=raw_bucket_name,
    gcp_conn_id="google_cloud_default",
    dag=dag,
)


# ============================================
# Task 3: Dataproc PySpark Job (Optional cluster provisioning)
# ============================================

submit_pyspark_job = DataprocSubmitPySparkJobOperator(
    task_id="submit_pyspark_job",
    main="file:///opt/airflow/spark/transform_reviews.py",
    cluster_name=os.environ.get("DATAPROC_CLUSTER_NAME", "customer-experience-cluster"),
    region=gcp_region,
    gcp_conn_id="google_cloud_default",
    arguments=[
        "--input", f"gs://{raw_bucket_name}/reviews.csv",
        "--output", f"gs://{trusted_bucket_name}/reviews",
        "--batch-id", "dag-run-{{ ds }}",
    ],
    dag=dag,
)


# ============================================
# Task 4: Load to BigQuery
# ============================================

load_to_bigquery = GCSToBigQuery(
    task_id="load_to_bigquery",
    bucket=trusted_bucket_name,
    source_objects=["reviews/*/*.parquet"],
    destination_project_dataset_table=f"{bq_dataset}.reviews",
    source_format="PARQUET",
    write_disposition="WRITE_TRUNCATE",
    autodetect=True,
    gcp_conn_id="google_cloud_default",
    dag=dag,
)


# ============================================
# Task 5: Run BigQuery Data Quality Checks
# ============================================

def run_bigquery_checks(**context):
    """Run basic post-load verification queries in BigQuery."""
    from google.cloud import bigquery
    
    client = bigquery.Client(project=gcp_project_id)
    table_id = f"{bq_dataset}.reviews"
    
    query = f"SELECT COUNT(*) as count FROM `{table_id}`"
    query_job = client.query(query)
    results = query_job.result()
    
    for row in results:
        logger.info(f"BigQuery record count: {row.count}")
    
    return True


bigquery_checks = PythonOperator(
    task_id="run_bigquery_checks",
    python_callable=run_bigquery_checks,
    dag=dag,
)


# ============================================
# Task Dependencies
# ============================================

generate_input_gcp >> upload_to_gcs_raw >> submit_pyspark_job >> load_to_bigquery >> bigquery_checks

