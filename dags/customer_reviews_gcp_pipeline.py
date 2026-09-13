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

def get_gcs_raw_bucket(**context):
    """Get GCS RAW bucket name from environment variable."""
    bucket = os.environ.get("GCS_RAW_BUCKET", "customer-experience-raw")
    logger.info(f"Using RAW bucket: {bucket}")
    return bucket


upload_to_gcs_raw = LocalToGoogleCloudStorageOperator(
    task_id="upload_to_gcs_raw",
    src=Path(__file__).parent.parent / "data" / "sample" / "reviews.csv",
    dst="reviews.csv",
    bucket="{{ task_instance.xcom_pull(task_ids='get_gcs_raw_bucket') }}",
    gcp_conn_id="google_cloud_default",
    dag=dag,
)

get_gcs_raw_bucket = PythonOperator(
    task_id="get_gcs_raw_bucket",
    python_callable=get_gcs_raw_bucket,
    dag=dag,
)

generate_input_gcp >> get_gcs_raw_bucket >> upload_to_gcs_raw


# ============================================
# Task 3: Create Dataproc Cluster (Optional)
# ============================================

def get_cluster_name(**context):
    """Generate unique cluster name."""
    import time
    return f"customer-experience-cluster-{int(time.time())}"


create_dataproc_cluster = DataprocCreateClusterOperator(
    task_id="create_dataproc_cluster",
    project_id=os.environ.get("GCP_PROJECT_ID", "your-project-id"),
    cluster_name="{{ task_instance.xcom_pull(task_ids='get_cluster_name') }}",
    region=os.environ.get("GCP_REGION", "us-central1"),
    gcp_conn_id="google_cloud_default",
    cluster_config={
        "master_config": {
            "num_instances": 1,
            "machine_type_uri": "n1-standard-2",
        },
        "worker_config": {
            "num_instances": 2,
            "machine_type_uri": "n1-standard-2",
        },
        "software_config": {
            "image_version": "2.2-debian10",
        },
    },
    dag=dag,
)

get_cluster_name = PythonOperator(
    task_id="get_cluster_name",
    python_callable=get_cluster_name,
    dag=dag,
)

# Only create cluster if requested (commented by default for cost savings)
# upload_to_gcs_raw >> create_dataproc_cluster


# ============================================
# Task 4: Submit PySpark Job
# ============================================

def get_gcs_trusted_bucket(**context):
    """Get GCS TRUSTED bucket name."""
    bucket = os.environ.get("GCS_TRUSTED_BUCKET", "customer-experience-trusted")
    logger.info(f"Using TRUSTED bucket: {bucket}")
    return bucket


submit_pyspark_job = DataprocSubmitPySparkJobOperator(
    task_id="submit_pyspark_job",
    main=f"file:///opt/airflow/spark/transform_reviews.py",
    cluster_name="{{ task_instance.xcom_pull(task_ids='get_cluster_name') }}",
    region=os.environ.get("GCP_REGION", "us-central1"),
    gcp_conn_id="google_cloud_default",
    arguments=[
        "--input", "gs://{{ task_instance.xcom_pull(task_ids='get_gcs_raw_bucket') }}/reviews.csv",
        "--output", "gs://{{ task_instance.xcom_pull(task_ids='get_gcs_trusted_bucket') }}/reviews",
        "--batch-id", "dag-run-{{ ds }}",
    ],
    dag=dag,
)

get_gcs_trusted_bucket = PythonOperator(
    task_id="get_gcs_trusted_bucket",
    python_callable=get_gcs_trusted_bucket,
    dag=dag,
)

# upload_to_gcs_raw >> submit_pyspark_job


# ============================================
# Task 5: Delete Dataproc Cluster
# ============================================

delete_dataproc_cluster = DataprocDeleteClusterOperator(
    task_id="delete_dataproc_cluster",
    cluster_name="{{ task_instance.xcom_pull(task_ids='get_cluster_name') }}",
    region=os.environ.get("GCP_REGION", "us-central1"),
    gcp_conn_id="google_cloud_default",
    dag=dag,
)

# submit_pyspark_job >> delete_dataproc_cluster


# ============================================
# Task 6: Load to BigQuery
# ============================================

def get_bigquery_dataset(**context):
    """Get BigQuery dataset name."""
    dataset = os.environ.get("BIGQUERY_DATASET", "customer_experience")
    logger.info(f"Using BigQuery dataset: {dataset}")
    return dataset


load_to_bigquery = GCSToBigQuery(
    task_id="load_to_bigquery",
    bucket="{{ task_instance.xcom_pull(task_ids='get_gcs_trusted_bucket') }}",
    source_objects=["reviews/*/*.parquet"],
    destination_project_dataset_table=f"{{{{ task_instance.xcom_pull(task_ids='get_bigquery_dataset') }}}}.reviews",
    source_format="PARQUET",
    write_disposition="WRITE_TRUNCATE",
    autodetect=True,
    gcp_conn_id="google_cloud_default",
    dag=dag,
)

get_bigquery_dataset = PythonOperator(
    task_id="get_bigquery_dataset",
    python_callable=get_bigquery_dataset,
    dag=dag,
)

# submit_pyspark_job >> load_to_bigquery


# ============================================
# Task 7: Run BigQuery Data Quality Checks
# ============================================

def run_bigquery_checks(**context):
    """Run data quality checks in BigQuery."""
    from google.cloud import bigquery
    
    client = bigquery.Client(
        project=os.environ.get("BIGQUERY_PROJECT", os.environ.get("GCP_PROJECT_ID"))
    )
    
    dataset_id = os.environ.get("BIGQUERY_DATASET", "customer_experience")
    table_id = f"{dataset_id}.reviews"
    
    # Check record count
    query = f"SELECT COUNT(*) as count FROM `{table_id}`"
    query_job = client.query(query)
    results = query_job.result()
    
    for row in results:
        logger.info(f"BigQuery record count: {row.count}")
    
    # Additional checks can be added here
    # See sql/data_quality.sql for example queries
    
    return results


bigquery_checks = PythonOperator(
    task_id="run_bigquery_checks",
    python_callable=run_bigquery_checks,
    dag=dag,
)

# load_to_bigquery >> bigquery_checks


# ============================================
# Task Dependencies
# ============================================

# Full pipeline with GCP (uncomment lines to enable)
generate_input_gcp >> get_gcs_raw_bucket >> upload_to_gcs_raw
# upload_to_gcs_raw >> get_cluster_name >> create_dataproc_cluster
# create_dataproc_cluster >> get_gcs_trusted_bucket >> submit_pyspark_job
# submit_pyspark_job >> delete_dataproc_cluster
# submit_pyspark_job >> load_to_bigquery >> bigquery_checks

# Simplified pipeline without Dataproc (for cost savings)
# upload_to_gcs_raw >> get_gcs_trusted_bucket >> load_to_bigquery >> bigquery_checks
