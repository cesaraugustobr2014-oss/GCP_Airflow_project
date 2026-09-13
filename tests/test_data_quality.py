#!/usr/bin/env python3
"""Tests for data quality checks."""

import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_quality.checks import (
    validate_schema,
    check_nulls,
    check_invalid_ratings,
    check_invalid_sources,
    check_duplicates,
    check_empty_text,
    run_all_validations
)


class TestValidateSchema:
    """Tests for validate_schema function."""

    def test_valid_schema(self):
        """Test with valid schema."""
        data = {
            "review_id": ["REV001"],
            "source": ["google_reviews"],
            "customer_id": ["CUS001"],
            "city": ["São Paulo"],
            "state": ["SP"],
            "country": ["BR"],
            "rating": [5],
            "review_text": ["Ótimo!"],
            "review_date": ["2026-01-01"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"],
        }
        df = pd.DataFrame(data)
        
        is_valid, errors = validate_schema(df)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_columns(self):
        """Test with missing columns."""
        data = {
            "review_id": ["REV001"],
            "source": ["google_reviews"],
        }
        df = pd.DataFrame(data)
        
        is_valid, errors = validate_schema(df)
        
        assert is_valid is False
        assert len(errors) > 0


class TestCheckNulls:
    """Tests for check_nulls function."""

    def test_no_nulls(self):
        """Test with no nulls."""
        data = {
            "review_id": ["REV001"],
            "source": ["google_reviews"],
            "rating": [5],
            "review_text": ["Ótimo!"],
        }
        df = pd.DataFrame(data)
        
        null_counts = check_nulls(df)
        
        assert null_counts["review_id"] == 0

    def test_with_nulls(self):
        """Test with null values."""
        data = {
            "review_id": ["REV001", None],
            "source": ["google_reviews", "tripadvisor"],
            "rating": [5, None],
        }
        df = pd.DataFrame(data)
        
        null_counts = check_nulls(df)
        
        assert null_counts["review_id"] == 1
        assert null_counts["rating"] == 1


class TestCheckInvalidRatings:
    """Tests for check_invalid_ratings function."""

    def test_valid_ratings(self):
        """Test with valid ratings."""
        data = {
            "review_id": ["REV001", "REV002"],
            "rating": [5, 3],
        }
        df = pd.DataFrame(data)
        
        count, records = check_invalid_ratings(df)
        
        assert count == 0
        assert len(records) == 0

    def test_invalid_ratings(self):
        """Test with invalid ratings."""
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "rating": [5, 0, 6],
        }
        df = pd.DataFrame(data)
        
        count, records = check_invalid_ratings(df)
        
        assert count == 2  # 0 and 6 are invalid


class TestCheckInvalidSources:
    """Tests for check_invalid_sources function."""

    def test_valid_sources(self):
        """Test with valid sources."""
        data = {
            "review_id": ["REV001", "REV002"],
            "source": ["google_reviews", "tripadvisor"],
        }
        df = pd.DataFrame(data)
        
        count, records = check_invalid_sources(df)
        
        assert count == 0

    def test_invalid_source(self):
        """Test with invalid source."""
        data = {
            "review_id": ["REV001", "REV002"],
            "source": ["google_reviews", "unknown_source"],
        }
        df = pd.DataFrame(data)
        
        count, records = check_invalid_sources(df)
        
        assert count == 1


class TestCheckDuplicates:
    """Tests for check_duplicates function."""

    def test_no_duplicates(self):
        """Test with no duplicates."""
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "source": ["google_reviews", "tripadvisor", "yelp"],
        }
        df = pd.DataFrame(data)
        
        count, ids = check_duplicates(df)
        
        assert count == 0

    def test_with_duplicates(self):
        """Test with duplicates."""
        data = {
            "review_id": ["REV001", "REV001", "REV002"],
            "source": ["google_reviews", "google_reviews", "tripadvisor"],
        }
        df = pd.DataFrame(data)
        
        count, ids = check_duplicates(df)
        
        assert count >= 1  # At least one duplicate


class TestRunAllValidations:
    """Tests for run_all_validations function."""

    def test_valid_dataset(self):
        """Test with valid dataset."""
        data = {
            "review_id": ["REV001", "REV002"],
            "source": ["google_reviews", "tripadvisor"],
            "customer_id": ["CUS001", "CUS002"],
            "city": ["São Paulo", "Rio"],
            "state": ["SP", "RJ"],
            "country": ["BR", "BR"],
            "rating": [5, 4],
            "review_text": ["Ótimo!", "Bom."],
            "review_date": ["2026-01-01", "2026-01-02"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 2,
        }
        df = pd.DataFrame(data)
        
        results = run_all_validations(df)
        
        assert results["is_valid"] is True
        assert results["total_records"] == 2

    def test_invalid_dataset(self):
        """Test with invalid dataset."""
        data = {
            "review_id": [None, "REV002"],
            "source": ["google_reviews", "unknown_source"],
            "customer_id": ["CUS001", "CUS002"],
            "city": ["São Paulo", "Rio"],
            "state": ["SP", "RJ"],
            "country": ["BR", "BR"],
            "rating": [5, 0],  # 0 is invalid
            "review_text": ["Ótimo!", "Bom."],
            "review_date": ["2026-01-01", "2026-01-02"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 2,
        }
        df = pd.DataFrame(data)
        
        results = run_all_validations(df)
        
        assert results["is_valid"] is False
