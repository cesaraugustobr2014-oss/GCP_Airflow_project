#!/usr/bin/env python3
"""
Data transformation and cleaning module.

This module provides functions to:
- Clean and normalize text data
- Handle null values
- Normalize casing and whitespace
- Standardize city/state/country
- Validate and fix ratings
"""

import logging
import re
from typing import Union
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if text is None or pd.isna(text):
        return ""
    
    # Convert to string
    text = str(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_source(source: str) -> str:
    """
    Normalize source name to lowercase and standard format.
    
    Args:
        source: Raw source string
        
    Returns:
        Normalized source name
    """
    if source is None:
        return "unknown"
    
    normalized = str(source).strip().lower()
    
    # Map common variations
    mappings = {
        "google review": "google_reviews",
        "google": "google_reviews",
        "tripadvisor review": "tripadvisor",
        "yelp review": "yelp",
        "social media": "social_media",
        "email feedback": "email",
        "email review": "email",
    }
    
    return mappings.get(normalized, normalized)


def normalize_city(city: str) -> str:
    """
    Normalize city name.
    
    Args:
        city: Raw city string
        
    Returns:
        Normalized city name
    """
    if city is None or pd.isna(city):
        return None
    
    return clean_text(city).title()


def normalize_state(state: str) -> str:
    """
    Normalize state abbreviation.
    
    Args:
        state: Raw state string
        
    Returns:
        Normalized state abbreviation (uppercase)
    """
    if state is None or pd.isna(state):
        return None
    
    normalized = str(state).strip().upper()
    
    # Validate Brazilian states
    valid_states = [
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
        "RS", "RO", "RR", "SC", "SP", "SE", "TO"
    ]
    
    return normalized if normalized in valid_states else None


def normalize_country(country: str) -> str:
    """
    Normalize country code.
    
    Args:
        country: Raw country string
        
    Returns:
        Normalized country code (uppercase)
    """
    if country is None or pd.isna(country):
        return None
    
    normalized = str(country).strip().upper()
    
    return normalized if normalized == "BR" else normalized


def validate_rating(rating) -> int:
    """
    Validate and normalize rating.
    
    Args:
        rating: Raw rating value
        
    Returns:
        Validated rating (1-5) or None if invalid
    """
    if rating is None or pd.isna(rating):
        return None
    
    try:
        rating_int = int(rating)
        if 1 <= rating_int <= 5:
            return rating_int
        else:
            return None
    except (ValueError, TypeError):
        return None


def convert_date(date_str: str) -> str:
    """
    Convert date string to ISO format.
    
    Args:
        date_str: Input date string
        
    Returns:
        Date in YYYY-MM-DD format or None if invalid
    """
    if date_str is None or pd.isna(date_str):
        return None
    
    import datetime
    
    date_str = str(date_str).strip()
    
    # Handle invalid dates
    if date_str.startswith("9999") or "-" not in date_str:
        return None
    
    try:
        # Try parsing YYYY-MM-DD
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        return None


def clean_dataframe(
    df: pd.DataFrame,
    drop_invalid_ratings: bool = False,
    drop_invalid_sources: bool = False,
    drop_null_text: bool = False
) -> pd.DataFrame:
    """
    Clean and transform a DataFrame of reviews.
    
    Args:
        df: Input DataFrame
        drop_invalid_ratings: Drop records with invalid ratings
        drop_invalid_sources: Drop records with invalid sources
        drop_null_text: Drop records with null review text
        
    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    
    initial_count = len(df_clean)
    logger.info(f"Starting with {initial_count} records")
    
    # Clean text fields
    df_clean["review_text"] = df_clean["review_text"].apply(clean_text)
    df_clean["city"] = df_clean["city"].apply(normalize_city)
    
    # Normalize source
    df_clean["source"] = df_clean["source"].apply(normalize_source)
    
    # Validate and fix rating
    invalid_ratings_before = df_clean["rating"].isna().sum()
    df_clean["rating"] = df_clean["rating"].apply(validate_rating)
    invalid_ratings_after = df_clean["rating"].isna().sum()
    
    logger.info(f"Invalid ratings: {invalid_ratings_before} before, {invalid_ratings_after} after")
    
    # Normalize state and country
    df_clean["state"] = df_clean["state"].apply(normalize_state)
    df_clean["country"] = df_clean["country"].apply(normalize_country)
    
    # Validate date
    df_clean["review_date_valid"] = df_clean["review_date"].apply(convert_date)
    
    # Filter based on rules
    original_count = len(df_clean)
    
    if drop_invalid_ratings:
        df_clean = df_clean.dropna(subset=["rating"])
        logger.info(f"Dropped records with invalid ratings: {original_count - len(df_clean)}")
        original_count = len(df_clean)
    
    if drop_invalid_sources:
        valid_sources = ["google_reviews", "tripadvisor", "yelp", "email", "social_media"]
        df_clean = df_clean[df_clean["source"].isin(valid_sources)]
        logger.info(f"Dropped records with invalid sources: {original_count - len(df_clean)}")
        original_count = len(df_clean)
    
    if drop_null_text:
        df_clean = df_clean[df_clean["review_text"].notna() & (df_clean["review_text"] != "")]
        logger.info(f"Dropped records with null/empty text: {original_count - len(df_clean)}")
    
    # Remove duplicates
    duplicates_before = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["review_id"])
    duplicates_removed = duplicates_before - len(df_clean)
    logger.info(f"Dropped {duplicates_removed} duplicate records")
    
    logger.info(f"Final count: {len(df_clean)} records (removed {initial_count - len(df_clean)})")
    
    return df_clean


# Example usage
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean and transform reviews data")
    parser.add_argument("input_csv", help="Input CSV file path")
    parser.add_argument("output_csv", help="Output cleaned CSV file path")
    parser.add_argument("--drop-invalid-ratings", action="store_true", help="Drop records with invalid ratings")
    parser.add_argument("--drop-invalid-sources", action="store_true", help="Drop records with invalid sources")
    parser.add_argument("--drop-null-text", action="store_true", help="Drop records with null text")
    
    args = parser.parse_args()
    
    print(f"Loading data from: {args.input_csv}")
    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} records\n")
    
    print("Cleaning data...")
    df_clean = clean_dataframe(
        df,
        drop_invalid_ratings=args.drop_invalid_ratings,
        drop_invalid_sources=args.drop_invalid_sources,
        drop_null_text=args.drop_null_text
    )
    
    print(f"\nSaving cleaned data to: {args.output_csv}")
    df_clean.to_csv(args.output_csv, index=False)
    print(f"✓ Saved {len(df_clean)} cleaned records")
    
    print("\nCleaned data sample:")
    print(df_clean.head(3).to_string())
