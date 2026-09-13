#!/usr/bin/env python3
"""Tests for data generation script."""

import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def test_generate_data_script_exists():
    """Verify the generate_sample_data.py script exists."""
    script_path = BASE_DIR / "scripts" / "generate_sample_data.py"
    assert script_path.exists(), "generate_sample_data.py should exist"


def test_data_directory_exists():
    """Verify the data sample directory exists."""
    data_dir = BASE_DIR / "data" / "sample"
    assert data_dir.exists(), "data/sample directory should exist"


def test_generate_data_creates_csv():
    """Verify that running the script creates a CSV file."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    # Generate data
    import subprocess
    result = subprocess.run(
        ["python3", "scripts/generate_sample_data.py"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert csv_path.exists(), "CSV file should be created"


def test_csv_has_expected_columns():
    """Verify the generated CSV has expected columns."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    expected_columns = [
        "review_id", "source", "customer_id", "city", "state", 
        "country", "rating", "review_text", "review_date", "ingestion_timestamp"
    ]
    
    assert all(col in df.columns for col in expected_columns), \
        f"CSV should have columns: {expected_columns}"


def test_csv_has_correct_record_count():
    """Verify the CSV has approximately 10,000 records."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    assert len(df) == 10000, f"Expected 10000 records, got {len(df)}"


def test_review_id_format():
    """Verify review_id follows expected format."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    # Check format: REV followed by 6 digits
    import re
    pattern = r"^REV\d{6}$"
    
    invalid_ids = df[~df["review_id"].str.match(pattern, na=False)]
    
    assert len(invalid_ids) == 0, f"Invalid review IDs found: {invalid_ids['review_id'].tolist()[:5]}"


def test_valid_sources():
    """Verify all sources are from the expected list."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    valid_sources = ["google_reviews", "tripadvisor", "yelp", "email", "social_media"]
    
    df["source_normalized"] = df["source"].str.strip().str.lower()
    
    invalid_sources = df[~df["source_normalized"].isin(valid_sources)]
    
    assert len(invalid_sources) == 0, f"Invalid sources found: {invalid_sources['source'].unique()}"


def test_rating_range():
    """Verify ratings are in valid range (1-5) for most records."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    # Most ratings should be 1-5
    valid_ratings = df[(df["rating"] >= 1) & (df["rating"] <= 5)]
    
    # Allow some invalid ratings (for testing data quality checks)
    assert len(valid_ratings) >= 9000, f"Most ratings should be in 1-5 range"


def test_date_format():
    """Verify review_date follows YYYY-MM-DD format."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    # Check basic date format
    import re
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    
    df["date_valid"] = df["review_date"].astype(str).str.match(pattern, na=False)
    
    # Most dates should match pattern
    assert df["date_valid"].mean() > 0.95, "Most dates should match YYYY-MM-DD format"


def test_data_quality_issues_present():
    """Verify that data quality issues are present in the dataset."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    df = pd.read_csv(csv_path)
    
    # Check for null texts
    null_texts = df["review_text"].isnull().sum()
    assert null_texts > 0, "Should have some null texts for testing"
    
    # Check for invalid ratings
    invalid_ratings = df[(df["rating"] < 1) | (df["rating"] > 5) | df["rating"].isna()].shape[0]
    assert invalid_ratings > 0, "Should have some invalid ratings for testing"
    
    # Check for missing cities
    missing_cities = df["city"].isnull().sum()
    assert missing_cities > 0, "Should have some missing cities for testing"


def test_generated_data_reproducible():
    """Verify that running the script multiple times produces same results (with seed)."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip("Run generate-data first")
    
    # Save original checksum
    import hashlib
    with open(csv_path, "rb") as f:
        original_hash = hashlib.md5(f.read()).hexdigest()
    
    # Regenerate
    import subprocess
    subprocess.run(
        ["python3", "scripts/generate_sample_data.py", "--num-records", "10000"],
        cwd=BASE_DIR,
        capture_output=True
    )
    
    # Compare checksums
    with open(csv_path, "rb") as f:
        new_hash = hashlib.md5(f.read()).hexdigest()
    
    assert original_hash == new_hash, "Data should be reproducible with same seed"
