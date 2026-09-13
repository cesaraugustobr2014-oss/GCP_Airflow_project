#!/usr/bin/env python3
"""Tests for data cleaning transformations."""

import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from transformations.clean_reviews import (
    clean_text,
    normalize_source,
    normalize_city,
    normalize_state,
    normalize_country,
    validate_rating,
    convert_date,
    clean_dataframe
)


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        text = "Hello World"
        assert clean_text(text) == "Hello World"

    def test_clean_text_whitespace(self):
        """Test whitespace removal."""
        text = "  Hello World  "
        assert clean_text(text) == "Hello World"

    def test_clean_text_extra_spaces(self):
        """Test multiple space normalization."""
        text = "Hello   World"
        assert clean_text(text) == "Hello World"

    def test_clean_text_none(self):
        """Test None input."""
        assert clean_text(None) == ""

    def test_clean_text_empty(self):
        """Test empty string."""
        assert clean_text("") == ""


class TestNormalizeSource:
    """Tests for normalize_source function."""

    def test_normalize_source_lowercase(self):
        """Test lowercase normalization."""
        assert normalize_source("GOOGLE_REVIEWS") == "google_reviews"

    def test_normalize_source_titlecase(self):
        """Test titlecase normalization."""
        assert normalize_source("Google_Reviews") == "google_reviews"

    def test_normalize_source_with_spaces(self):
        """Test spaces in source name."""
        assert normalize_source("Google Reviews") == "google reviews"

    def test_normalize_source_unknown(self):
        """Test unknown source."""
        assert normalize_source("unknown_source") == "unknown_source"

    def test_normalize_source_none(self):
        """Test None input."""
        assert normalize_source(None) == "unknown"


class TestValidateRating:
    """Tests for validate_rating function."""

    def test_valid_rating_1(self):
        """Test rating 1."""
        assert validate_rating(1) == 1

    def test_valid_rating_5(self):
        """Test rating 5."""
        assert validate_rating(5) == 5

    def test_invalid_rating_zero(self):
        """Test rating 0."""
        assert validate_rating(0) is None

    def test_invalid_rating_six(self):
        """Test rating 6."""
        assert validate_rating(6) is None

    def test_invalid_rating_negative(self):
        """Test negative rating."""
        assert validate_rating(-1) is None

    def test_invalid_rating_string(self):
        """Test invalid string rating."""
        assert validate_rating("invalid") is None

    def test_invalid_rating_none(self):
        """Test None rating."""
        assert validate_rating(None) is None


class TestCleanDataFrame:
    """Tests for clean_dataframe function."""

    def test_clean_dataframe_basic(self):
        """Test basic cleaning."""
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "source": ["google_reviews", "tripadvisor", "yelp"],
            "customer_id": ["CUS001", "CUS002", "CUS003"],
            "city": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"],
            "state": ["SP", "RJ", "MG"],
            "country": ["BR", "BR", "BR"],
            "rating": [5, 4, 3],
            "review_text": ["Ótimo!", "Bom.", "Ruim."],
            "review_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 3,
        }
        df = pd.DataFrame(data)
        
        df_clean = clean_dataframe(df)
        
        assert len(df_clean) == 3
        assert "sentiment" not in df_clean.columns  # Should not add sentiment

    def test_clean_dataframe_invalid_rating(self):
        """Test filtering invalid ratings."""
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "source": ["google_reviews", "tripadvisor", "yelp"],
            "customer_id": ["CUS001", "CUS002", "CUS003"],
            "city": ["São Paulo", "Rio", "Belo"],
            "state": ["SP", "RJ", "MG"],
            "country": ["BR", "BR", "BR"],
            "rating": [5, 0, 3],  # 0 is invalid
            "review_text": ["Ótimo!", "Bom.", "Ruim."],
            "review_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 3,
        }
        df = pd.DataFrame(data)
        
        df_clean = clean_dataframe(df, drop_invalid_ratings=True)
        
        assert len(df_clean) == 2  # Should drop REV002

    def test_clean_dataframe_duplicates(self):
        """Test duplicate removal."""
        data = {
            "review_id": ["REV001", "REV001", "REV002"],
            "source": ["google_reviews", "google_reviews", "tripadvisor"],
            "customer_id": ["CUS001", "CUS001", "CUS002"],
            "city": ["São Paulo", "São Paulo", "Rio"],
            "state": ["SP", "SP", "RJ"],
            "country": ["BR", "BR", "BR"],
            "rating": [5, 5, 4],
            "review_text": ["Ótimo!", "Ótimo!", "Bom."],
            "review_date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 3,
        }
        df = pd.DataFrame(data)
        
        df_clean = clean_dataframe(df)
        
        assert len(df_clean) == 2  # Should remove one duplicate

    def test_clean_dataframe_empty_text(self):
        """Test filtering empty text."""
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "source": ["google_reviews", "tripadvisor", "yelp"],
            "customer_id": ["CUS001", "CUS002", "CUS003"],
            "city": ["São Paulo", "Rio", "Belo"],
            "state": ["SP", "RJ", "MG"],
            "country": ["BR", "BR", "BR"],
            "rating": [5, 4, 3],
            "review_text": ["Ótimo!", "", "Ruim."],
            "review_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "ingestion_timestamp": ["2026-01-04T10:00:00"] * 3,
        }
        df = pd.DataFrame(data)
        
        df_clean = clean_dataframe(df, drop_null_text=True)
        
        assert len(df_clean) == 2  # Should drop REV002
