#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Customer Experience Data Pipeline tests.
"""

import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


@pytest.fixture
def sample_reviews_df():
    """Load sample reviews for testing."""
    csv_path = BASE_DIR / "data" / "sample" / "reviews.csv"
    
    if not csv_path.exists():
        pytest.skip(f"Sample data not found at {csv_path}. Run: make generate-data")
    
    df = pd.read_csv(csv_path)
    return df


@pytest.fixture
def minimal_reviews_df():
    """Create a minimal DataFrame for testing transformations."""
    data = {
        "review_id": ["REV001", "REV002", "REV003"],
        "source": ["google_reviews", "tripadvisor", "yelp"],
        "customer_id": ["CUS001", "CUS002", "CUS003"],
        "city": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"],
        "state": ["SP", "RJ", "MG"],
        "country": ["BR", "BR", "BR"],
        "rating": [5, 4, 3],
        "review_text": ["Ótimo serviço!", "Bom, mas poderia melhorar.", "Ruim, vou evitar."],
        "review_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "ingestion_timestamp": ["2026-01-04T10:00:00", "2026-01-04T10:00:00", "2026-01-04T10:00:00"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def reviews_with_issues_df():
    """Create a DataFrame with intentional data quality issues."""
    data = {
        "review_id": ["REV001", "REV001", "REV002", "REV003", "REV004", "REV005", None],
        "source": ["GOOGLE_REVIEWS", "Google_Reviews", "unknown_source", "email", "Social_Media", "", None],
        "customer_id": ["CUS001", "CUS001", "CUS002", None, "CUS004", "CUS005", "CUS006"],
        "city": ["São Paulo", "São Paulo", None, "Rio", "Belo Horizonte", "Curitiba", "Salvador"],
        "state": ["SP", "SP", "RJ", None, "MG", "PR", "BA"],
        "country": ["BR", "BR", "BR", "BR", "BR", "BR", "BR"],
        "rating": [5, 5, 6, 1, "invalid", 3, 4],
        "review_text": ["Ótimo!", "Ótimo!", "", None, "Bom serviço", "Muito bom", "Ruim"],
        "review_date": ["2026-01-01", "2026-01-01", "invalid-date", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
        "ingestion_timestamp": ["2026-01-04T10:00:00"] * 7,
    }
    return pd.DataFrame(data)
