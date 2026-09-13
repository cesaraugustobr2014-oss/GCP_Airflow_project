#!/usr/bin/env python3
"""
Customer Reviews Local Pipeline - Apache Airflow DAG.

This DAG orchestrates the complete customer reviews data pipeline:
1. Generate or detect input data
2. Ingest reviews from CSV
3. Validate raw data
4. Transform and clean data
5. Calculate sentiment
6. Write to trusted layer
7. Create curated dataset
8. Run data quality checks

This DAG runs locally with LocalExecutor (no GCP required).
For GCP integration, use customer_reviews_gcp_pipeline.py
"""

import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ingestion.ingest_reviews import read_reviews_csv, add_ingestion_metadata, write_raw_layer
from data_quality.checks import run_all_validations
from transformations.clean_reviews import clean_dataframe
from transformations.sentiment_analysis import analyze_dataframe


# Default arguments for DAG
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": days_ago(1),
}

# DAG configuration
dag = DAG(
    dag_id="customer_reviews_local_pipeline",
    default_args=default_args,
    description="Local pipeline for processing customer reviews",
    schedule_interval="@daily",
    catchup=False,
)


def gen_or_detect_input(**context):
    """Generate sample data or detect existing data."""
    import subprocess
    from pathlib import Path
    
    script_path = Path(__file__).parent.parent / "scripts" / "generate_sample_data.py"
    output_path = Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"
    
    # Generate data if it doesn't exist
    if not output_path.exists():
        print(f"Generating sample data at {output_path}")
        subprocess.run(
            ["python3", str(script_path), "--num-records", "10000"],
            cwd=Path(__file__).parent.parent,
            check=True,
        )
    
    return str(output_path)


def ingest_reviews_task(**context):
    """Ingest reviews from CSV and write to RAW layer."""
    import pandas as pd
    from pathlib import Path
    
    # Get input path from previous task
    input_path = Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read CSV
    df = read_reviews_csv(input_path, use_pandas=True)
    print(f"Loaded {len(df)} records from CSV")
    
    # Add metadata
    df = add_ingestion_metadata(df)
    
    # Write to RAW layer
    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    count = write_raw_layer(df, raw_dir)
    
    print(f"Wrote {count} records to RAW layer")
    
    # Push to XCom
    context["ti"].xcom_push(key="record_count", value=count)
    
    return str(raw_dir)


def validate_raw_task(**context):
    """Validate raw data and check quality."""
    from pathlib import Path
    
    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    reviews_path = raw_dir / "reviews"
    
    if not reviews_path.exists():
        raise FileNotFoundError(f"RAW layer not found: {reviews_path}")
    
    # Read Parquet data
    import pyarrow.parquet as pq
    table = pq.read_table(reviews_path)
    df = table.to_pandas()
    
    print(f"Read {len(df)} records from RAW layer")
    
    # Run validations
    results = run_all_validations(df)
    
    # Log results
    print(f"Validation results: {results}")
    
    # Push results to XCom
    context["ti"].xcom_push(key="validation_results", value=results)
    
    # Fail if critical validation failed
    if not results.get("is_valid", False):
        raise ValueError("Data validation failed")
    
    return results


def transform_reviews_task(**context):
    """Transform and clean reviews data."""
    from pathlib import Path
    import pandas as pd
    import pyarrow.parquet as pq
    
    # Read from RAW layer
    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    reviews_path = raw_dir / "reviews"
    
    table = pq.read_table(reviews_path)
    df = table.to_pandas()
    
    print(f"Transforming {len(df)} records")
    
    # Clean data
    df_clean = clean_dataframe(df, drop_invalid_ratings=True, drop_invalid_sources=True, drop_null_text=True)
    
    print(f"After cleaning: {len(df_clean)} records")
    
    # Write to TRUSTED layer
    trusted_dir = Path(__file__).parent.parent / "data" / "trusted"
    trusted_path = trusted_dir / "reviews"
    trusted_path.mkdir(parents=True, exist_ok=True)
    
    # Convert to PySpark for Parquet writing
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    df_spark = spark.createDataFrame(df_clean)
    
    # Add partition columns
    from pyspark.sql.functions import current_date, year, month, dayofmonth, lpad, concat
    df_spark = df_spark.withColumn("ingestion_year", year(current_date()))
    df_spark = df_spark.withColumn("ingestion_month", lpad(month(current_date()), 2, "0"))
    df_spark = df_spark.withColumn("ingestion_day", lpad(dayofmonth(current_date()), 2, "0"))
    
    df_spark.write.mode("overwrite").partitionBy("ingestion_year", "ingestion_month", "ingestion_day").parquet(str(trusted_path))
    
    print(f"Wrote {len(df_clean)} records to TRUSTED layer")
    
    context["ti"].xcom_push(key="transformed_count", value=len(df_clean))
    
    return str(trusted_path)


def calculate_sentiment_task(**context):
    """Calculate sentiment for transformed reviews."""
    from pathlib import Path
    import pandas as pd
    from pyspark.sql import SparkSession
    
    # Read from TRUSTED layer
    trusted_dir = Path(__file__).parent.parent / "data" / "trusted"
    reviews_path = trusted_dir / "reviews"
    
    spark = SparkSession.builder.getOrCreate()
    df_spark = spark.read.parquet(str(reviews_path))
    
    df = df_spark.toPandas()
    
    print(f"Calculating sentiment for {len(df)} records")
    
    # Calculate sentiment
    df_with_sentiment = analyze_dataframe(df, text_column="review_text")
    
    print("Sentiment distribution:")
    print(df_with_sentiment["sentiment"].value_counts())
    
    # Write to CURATED layer
    curated_dir = Path(__file__).parent.parent / "data" / "curated"
    curated_path = curated_dir / "customer_sentiment"
    curated_path.mkdir(parents=True, exist_ok=True)
    
    # Write Parquet
    df_spark_curated = spark.createDataFrame(df_with_sentiment)
    df_spark_curated.write.mode("overwrite").parquet(str(curated_path))
    
    print(f"Wrote {len(df_with_sentiment)} records to CURATED layer")
    
    context["ti"].xcom_push(key="sentiment_count", value=len(df_with_sentiment))
    
    # Log sentiment summary
    from transformations.sentiment_analysis import generate_sentiment_summary
    print(generate_sentiment_summary(df_with_sentiment))
    
    return str(curated_path)


def run_data_quality_task(**context):
    """Run final data quality checks on curated data."""
    from pathlib import Path
    import pandas as pd
    
    curated_dir = Path(__file__).parent.parent / "data" / "curated"
    reviews_path = curated_dir / "customer_sentiment"
    
    # Read curated data
    df = pd.read_parquet(reviews_path)
    
    print(f"Running final quality checks on {len(df)} records")
    
    # Check key metrics
    total_records = len(df)
    positive_count = (df["sentiment"] == "POSITIVE").sum()
    neutral_count = (df["sentiment"] == "NEUTRAL").sum()
    negative_count = (df["sentiment"] == "NEGATIVE").sum()
    
    print(f"Total records: {total_records}")
    print(f"Positive: {positive_count} ({positive_count/total_records*100:.1f}%)")
    print(f"Neutral: {neutral_count} ({neutral_count/total_records*100:.1f}%)")
    print(f"Negative: {negative_count} ({negative_count/total_records*100:.1f}%)")
    
    context["ti"].xcom_push(key="final_count", value=total_records)
    context["ti"].xcom_push(key="sentiment_breakdown", value={
        "positive": positive_count,
        "neutral": neutral_count,
        "negative": negative_count,
    })
    
    return total_records


# Define pipeline tasks

generate_input = PythonOperator(
    task_id="generate_or_detect_input",
    python_callable=gen_or_detect_input,
    dag=dag,
)

ingest_reviews = PythonOperator(
    task_id="ingest_reviews",
    python_callable=ingest_reviews_task,
    dag=dag,
)

validate_raw = PythonOperator(
    task_id="validate_raw_data",
    python_callable=validate_raw_task,
    dag=dag,
)

transform_reviews = PythonOperator(
    task_id="transform_reviews",
    python_callable=transform_reviews_task,
    dag=dag,
)

calculate_sentiment = PythonOperator(
    task_id="calculate_sentiment",
    python_callable=calculate_sentiment_task,
    dag=dag,
)

run_quality_checks = PythonOperator(
    task_id="run_data_quality_checks",
    python_callable=run_data_quality_task,
    dag=dag,
)

# Define task dependencies

generate_input >> ingest_reviews >> validate_raw >> transform_reviews >> calculate_sentiment >> run_quality_checks

# Task documentation
generate_input.doc = "Generate sample data or detect existing data"
ingest_reviews.doc = "Ingest reviews from CSV and write to RAW layer"
validate_raw.doc = "Validate raw data and check data quality"
transform_reviews.doc = "Transform and clean reviews data"
calculate_sentiment.doc = "Calculate sentiment using VADER"
run_quality_checks.doc = "Run final data quality checks"
