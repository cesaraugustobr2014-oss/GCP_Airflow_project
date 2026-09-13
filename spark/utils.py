#!/usr/bin/env python3
"""
Create a local SparkSession for development and testing.

This module provides a helper function to create a SparkSession
configured for local development without requiring a Spark cluster.
"""

from pyspark.sql import SparkSession
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_spark_session(app_name: str = "CustomerExperience") -> SparkSession:
    """
    Create a SparkSession configured for local development.
    
    Args:
        app_name: Name of the Spark application
        
    Returns:
        Configured SparkSession
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    logger.info(f"Created SparkSession: {app_name}")
    return spark


def stop_spark_session(spark: SparkSession) -> None:
    """
    Stop a SparkSession and clean up resources.
    
    Args:
        spark: SparkSession to stop
    """
    spark.stop()
    logger.info("SparkSession stopped")


# Example usage
if __name__ == "__main__":
    # Create session
    spark = get_spark_session("TestSession")
    
    # Test basic operation
    df = spark.createDataFrame([(1, "test"), (2, "data")], ["id", "value"])
    print(f"Created DataFrame with {df.count()} rows")
    
    # Test reading CSV
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    data_path = Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"
    if data_path.exists():
        df_reviews = spark.read.csv(str(data_path), header=True, inferSchema=True)
        print(f"Loaded reviews: {df_reviews.count()} rows")
    
    # Stop session
    stop_spark_session(spark)
