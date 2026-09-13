#!/usr/bin/env python3
"""
Ingestion module for reading reviews data and writing to data lake layers.

This module provides functions to:
- Read customer reviews from CSV or GCS
- Write data to RAW layer (Parquet format)
- Handle metadata ( ingestion_timestamp, source)

Usage:
    import ingestion.ingest_reviews
    
    # Read from local CSV
    df = ingest_reviews.read_reviews_csv("data/sample/reviews.csv")
    
    # Write to RAW layer
    ingest_reviews.write_raw_layer(df, "data/raw")
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from pyspark.sql import SparkSession, DataFrame
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Supported sources
SUPPORTED_SOURCES = [
    "google_reviews",
    "tripadvisor",
    "yelp",
    "email",
    "social_media"
]


def read_reviews_csv(
    file_path: Union[str, Path],
    spark: Optional[SparkSession] = None,
    use_pandas: bool = False
) -> Union[pd.DataFrame, DataFrame]:
    """
    Read reviews from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        spark: SparkSession (optional, used if use_pandas=False)
        use_pandas: If True, use pandas instead of PySpark
        
    Returns:
        DataFrame with reviews data
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Reading reviews from: {file_path}")
    
    if use_pandas or spark is None:
        # Use pandas (simpler for local development)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records using pandas")
        return df
    else:
        # Use PySpark
        df = spark.read.csv(
            str(file_path),
            header=True,
            inferSchema=True
        )
        logger.info(f"Loaded {df.count()} records using PySpark")
        return df


def add_ingestion_metadata(df: Union[pd.DataFrame, DataFrame]) -> Union[pd.DataFrame, DataFrame]:
    """
    Add ingestion metadata to the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with ingestion_timestamp and source columns added
    """
    if isinstance(df, pd.DataFrame):
        df = df.copy()
        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        df["ingestion_timestamp"] = current_timestamp
        # Extract source from filename if available
        if "source" not in df.columns:
            df["source"] = "unknown"
    else:
        from pyspark.sql.functions import current_timestamp, lit
        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        df = df.withColumn("ingestion_timestamp", lit(current_timestamp))
        if "source" not in df.columns:
            df = df.withColumn("source", lit("unknown"))
    
    logger.info("Added ingestion metadata")
    return df


def write_raw_layer(df: Union[pd.DataFrame, DataFrame], output_path: Union[str, Path]) -> int:
    """
    Write data to the RAW layer in Parquet format, partitioned by date.
    
    Args:
        df: DataFrame to write
        output_path: Base path for raw data
        
    Returns:
        Number of records written
    """
    output_path = Path(output_path) / "reviews"
    
    if isinstance(df, pd.DataFrame):
        # Convert to PySpark for Parquet writing
        spark = SparkSession.builder.getOrCreate()
        df_spark = spark.createDataFrame(df)
        
        # Add date partition columns
        from pyspark.sql.functions import to_date, col
        df_spark = df_spark.withColumn(
            "ingestion_date",
            to_date(col("ingestion_timestamp"))
        )
        
        # Write as Parquet, partitioned by date
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get current date for partition
        current_date = datetime.now().strftime("%Y/%m/%d")
        partition_path = output_path / f"year={current_date[:4]}" / f"month={current_date[5:7]}" / f"day={current_date[8:10]}"
        partition_path.mkdir(parents=True, exist_ok=True)
        
        df_spark.write.mode("overwrite").parquet(str(partition_path))
        
        count = len(df)
    else:
        # PySpark DataFrame
        from pyspark.sql.functions import year, month, dayofmonth, col
        
        df_with_date = df.withColumn("ingestion_year", year(col("ingestion_timestamp")))
        df_with_date = df_with_date.withColumn("ingestion_month", month(col("ingestion_timestamp")))
        df_with_date = df_with_date.withColumn("ingestion_day", dayofmonth(col("ingestion_timestamp")))
        
        # Write to partitioned path
        output_path.mkdir(parents=True, exist_ok=True)
        
        df_with_date.write.mode("overwrite").partitionBy(
            "ingestion_year", "ingestion_month", "ingestion_day"
        ).parquet(str(output_path))
        
        count = df.count()
    
    logger.info(f"✓ Written {count} records to RAW layer: {output_path}")
    return count


def read_raw_layer(output_path: Union[str, Path], spark: SparkSession) -> DataFrame:
    """
    Read data from the RAW layer.
    
    Args:
        output_path: Base path for raw data
        spark: SparkSession
        
    Returns:
        DataFrame with raw data
    """
    raw_path = Path(output_path) / "reviews"
    
    if not raw_path.exists():
        logger.warning(f"RAW layer not found: {raw_path}")
        return spark.emptyDataFrame
    
    df = spark.read.parquet(str(raw_path))
    logger.info(f"✓ Read {df.count()} records from RAW layer")
    return df


def list_raw_partitions(output_path: Union[str, Path]) -> list:
    """
    List all partitions in the RAW layer.
    
    Args:
        output_path: Base path for raw data
        
    Returns:
        List of partition paths
    """
    raw_path = Path(output_path) / "reviews"
    
    if not raw_path.exists():
        return []
    
    partitions = []
    for year_dir in raw_path.glob("year=*"):
        for month_dir in year_dir.glob("month=*"):
            for day_dir in month_dir.glob("day=*"):
                partitions.append(str(day_dir))
    
    logger.info(f"Found {len(partitions)} partitions in RAW layer")
    return partitions


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.ingest_reviews [csv_file_path]")
        print("  If no path provided, uses default: data/sample/reviews.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample/reviews.csv"
    raw_path = "data/raw"
    
    print(f"Ingesting reviews from: {csv_path}")
    print(f"Writing to RAW layer: {raw_path}")
    
    # Read CSV
    df = read_reviews_csv(csv_path, use_pandas=True)
    print(f"Loaded {len(df)} records")
    
    # Add metadata
    df = add_ingestion_metadata(df)
    print("Added ingestion metadata")
    
    # Write to RAW layer
    count = write_raw_layer(df, raw_path)
    print(f"✓ Total records processed: {count}")
