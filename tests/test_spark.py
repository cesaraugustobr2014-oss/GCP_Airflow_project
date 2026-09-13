#!/usr/bin/env python3
"""Tests for Spark transformation job."""

import pytest
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_spark_job_exists():
    """Verify transform_reviews.py exists."""
    job_path = Path(__file__).parent.parent / "spark" / "transform_reviews.py"
    assert job_path.exists(), "Spark job should exist"


def test_spark_utils_exists():
    """Verify utils.py exists."""
    utils_path = Path(__file__).parent.parent / "spark" / "utils.py"
    assert utils_path.exists(), "Spark utils should exist"


def test_spark_session_creation():
    """Test Spark session creation."""
    pytest.importorskip("pyspark")
    
    from spark.utils import get_spark_session, stop_spark_session
    
    spark = get_spark_session("TestSession")
    assert spark is not None
    assert spark.version is not None
    
    stop_spark_session(spark)


def test_spark_read_csv():
    """Test reading CSV with Spark."""
    pytest.importorskip("pyspark")
    
    from spark.utils import get_spark_session, stop_spark_session
    from pathlib import Path
    
    spark = get_spark_session("TestCSV")
    
    csv_path = Path(__file__).parent.parent / "data" / "sample" / "reviews.csv"
    
    if csv_path.exists():
        df = spark.read.csv(str(csv_path), header=True, inferSchema=True)
        assert df.count() > 0
        assert "review_id" in df.columns
    
    stop_spark_session(spark)


def test_spark_data_operations():
    """Test basic Spark data operations."""
    pytest.importorskip("pyspark")
    
    from spark.utils import get_spark_session, stop_spark_session
    
    spark = get_spark_session("TestDataOps")
    
    # Create test DataFrame
    data = [
        (1, "test1"),
        (2, "test2"),
        (3, "test3"),
    ]
    
    df = spark.createDataFrame(data, ["id", "value"])
    
    assert df.count() == 3
    assert df.filter(df.id == 1).count() == 1
    
    stop_spark_session(spark)
