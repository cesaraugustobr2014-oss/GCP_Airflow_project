#!/usr/bin/env python3
"""
Spark transformation job for customer reviews.

This PySpark job:
1. Reads raw reviews data from Parquet
2. Validates and cleans records
3. Normalizes data (sources, cities, ratings)
4. Removes duplicates
5. Writes to trusted layer

Usage:
    spark-submit spark/transform_reviews.py \
        --input data/raw/reviews \
        --output data/trusted/reviews \
        --batch-id 20260912
"""

import argparse
import logging
from typing import Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lower, trim, when, lit, current_timestamp, year, month, dayofmonth,
    concat, lpad
)
from pyspark.sql.types import IntegerType, StringType, BooleanType
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Valid sources
VALID_SOURCES = [
    "google_reviews",
    "tripadvisor",
    "yelp",
    "email",
    "social_media"
]

# Valid Brazilian states
VALID_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]


def validate_rating(rating_col) -> DataFrame:
    """Create a validated rating column (1-5)."""
    return when(
        (col(rating_col).isNull()) | 
        (col(rating_col) < 1) | 
        (col(rating_col) > 5),
        lit(None).cast(IntegerType())
    ).otherwise(col(rating_col).cast(IntegerType()))


def normalize_source(source_col) -> DataFrame:
    """Normalize source to lowercase and standard format."""
    mappings = {
        "google reviews": "google_reviews",
        "google": "google_reviews",
        "tripadvisor review": "tripadvisor",
        "yelp review": "yelp",
        "social media": "social_media",
        "email feedback": "email",
        "email review": "email",
    }
    
    normalized = lower(trim(col(source_col)))
    
    for invalid, valid in mappings.items():
        normalized = when(normalized == invalid, valid).otherwise(normalized)
    
    return normalized


def normalize_city(city_col) -> DataFrame:
    """Normalize city name to title case."""
    return when(col(city_col).isNull(), lit(None)).otherwise(
        concat(
            col(city_col).substr(1, 1),
            lower(col(city_col).substr(2, 1000))
        )
    )


def normalize_state(state_col) -> DataFrame:
    """Normalize state to uppercase."""
    return when(col(state_col).isNull(), lit(None)).otherwise(
        upper(trim(col(state_col)))
    )


def normalize_country(country_col) -> DataFrame:
    """Normalize country code."""
    return when(col(country_col).isNull(), lit(None)).otherwise(
        upper(trim(col(country_col)))
    )


def clean_reviews(df: DataFrame) -> DataFrame:
    """
    Apply all cleaning transformations to the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    # Normalize text fields
    df_clean = df.withColumn("source", normalize_source("source"))
    df_clean = df_clean.withColumn("city", normalize_city("city"))
    df_clean = df_clean.withColumn("state", normalize_state("state"))
    df_clean = df_clean.withColumn("country", normalize_country("country"))
    
    # Validate rating
    df_clean = df_clean.withColumn("rating_valid", validate_rating("rating"))
    
    # Validate source
    df_clean = df_clean.withColumn(
        "source_valid",
        when(col("source").isin(VALID_SOURCES), lit(True)).otherwise(lit(False))
    )
    
    # Clean review text
    df_clean = df_clean.withColumn("review_text_clean", trim(col("review_text")))
    
    # Validate text is not empty
    df_clean = df_clean.withColumn(
        "text_valid",
        when(
            (col("review_text_clean").isNull()) |
            (col("review_text_clean") == ""),
            lit(False)
        ).otherwise(lit(True))
    )
    
    return df_clean


def remove_duplicates(df: DataFrame, id_col: str = "review_id") -> DataFrame:
    """
    Remove duplicate records by ID, keeping the first occurrence.
    
    Args:
        df: Input DataFrame
        id_col: Column to use for deduplication
        
    Returns:
        Deduplicated DataFrame
    """
    window_spec = Window.orderBy(id_col)
    
    df_deduped = df.withColumn("row_num", row_number().over(window_spec))
    df_deduped = df_deduped.filter(col("row_num") == 1).drop("row_num")
    
    duplicates_removed = df.count() - df_deduped.count()
    logger.info(f"Removed {duplicates_removed} duplicate records")
    
    return df_deduped


def filter_valid_records(df: DataFrame) -> DataFrame:
    """
    Filter to keep only valid records.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    # Keep records with valid rating, source, and text
    df_valid = df.filter(
        (col("rating_valid").isNotNull()) &
        (col("source_valid") == lit(True)) &
        (col("text_valid") == lit(True))
    )
    
    filtered_count = df.count() - df_valid.count()
    logger.info(f"Filtered out {filtered_count} invalid records")
    
    return df_valid


def add_partition_columns(df: DataFrame) -> DataFrame:
    """
    Add partition columns for writing to data lake.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with partition columns
    """
    from pyspark.sql.functions import current_date
    
    # Add ingestion date partition
    df_partitioned = df.withColumn("ingestion_year", year(current_date()))
    df_partitioned = df_partitioned.withColumn("ingestion_month", lpad(month(current_date()), 2, "0"))
    df_partitioned = df_partitioned.withColumn("ingestion_day", lpad(dayofmonth(current_date()), 2, "0"))
    
    return df_partitioned


def write_trusted_layer(df: DataFrame, output_path: str) -> None:
    """
    Write processed data to trusted layer in Parquet format.
    
    Args:
        df: DataFrame to write
        output_path: Output directory path
    """
    # Drop internal columns
    df_output = df.drop("source_valid", "text_valid", "rating_valid")
    
    # Write partitioned by ingestion date
    df_output.write.mode("overwrite").partitionBy(
        "ingestion_year", "ingestion_month", "ingestion_day"
    ).parquet(output_path)
    
    logger.info(f"✓ Written {df_output.count()} records to trusted layer: {output_path}")


def run_pipeline(
    input_path: str,
    output_path: str,
    batch_id: Optional[str] = None
) -> None:
    """
    Run the full Spark transformation pipeline.
    
    Args:
        input_path: Path to raw data (Parquet)
        output_path: Path for trusted data (Parquet)
        batch_id: Optional batch identifier for logging
    """
    spark = SparkSession.builder \
        .appName(f"CustomerReviewsTransform-{batch_id or 'default'}") \
        .getOrCreate()
    
    try:
        # Read raw data
        logger.info(f"Reading raw data from: {input_path}")
        df_raw = spark.read.parquet(input_path)
        initial_count = df_raw.count()
        logger.info(f"Read {initial_count} records from raw layer")
        
        # Apply cleaning
        logger.info("Applying cleaning transformations...")
        df_cleaned = clean_reviews(df_raw)
        
        # Remove duplicates
        logger.info("Removing duplicates...")
        df_deduped = remove_duplicates(df_cleaned)
        
        # Filter valid records
        logger.info("Filtering valid records...")
        df_valid = filter_valid_records(df_deduped)
        
        # Add partition columns
        logger.info("Adding partition columns...")
        df_partitioned = add_partition_columns(df_valid)
        
        # Write to trusted layer
        logger.info("Writing to trusted layer...")
        write_trusted_layer(df_partitioned, output_path)
        
        # Log summary
        final_count = df_partitioned.count()
        logger.info(f"Pipeline complete. Processed {final_count} valid records")
        
    finally:
        spark.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Spark transformation job for customer reviews")
    parser.add_argument("--input", required=True, help="Input path (raw data Parquet)")
    parser.add_argument("--output", required=True, help="Output path (trusted data Parquet)")
    parser.add_argument("--batch-id", default=None, help="Batch identifier for logging")
    
    args = parser.parse_args()
    
    logger.info(f"Starting transformation pipeline")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    
    run_pipeline(args.input, args.output, args.batch_id)


if __name__ == "__main__":
    main()
