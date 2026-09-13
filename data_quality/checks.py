#!/usr/bin/env python3
"""
Data validation and quality checks for customer reviews.

This module provides functions to:
- Validate schema and data types
- Check for nulls and invalid values
- Detect duplicates
- Generate quality metrics

Validation Rules:
- review_id: Not null, unique
- source: Must be in supported list
- rating: Integer between 1 and 5
- review_text: Not null or empty after cleaning
- review_date: Valid date format
- customer_id: Not null
"""

import logging
from typing import Dict, List, Tuple, Union
from pyspark.sql import DataFrame
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Valid values
VALID_SOURCES = [
    "google_reviews",
    "tripadvisor",
    "yelp",
    "email",
    "social_media"
]

VALID_SENTIMENTS = ["POSITIVE", "NEUTRAL", "NEGATIVE"]

# Schema requirements
SCHEMA_REQUIREMENTS = {
    "review_id": {"type": "string", "nullable": False},
    "source": {"type": "string", "nullable": False, "valid_values": VALID_SOURCES},
    "customer_id": {"type": "string", "nullable": False},
    "city": {"type": "string", "nullable": True},
    "state": {"type": "string", "nullable": True},
    "country": {"type": "string", "nullable": True},
    "rating": {"type": "integer", "nullable": False, "min": 1, "max": 5},
    "review_text": {"type": "string", "nullable": False},
    "review_date": {"type": "date", "nullable": False},
    "ingestion_timestamp": {"type": "timestamp", "nullable": False},
}


def validate_schema(
    df: Union[pd.DataFrame, DataFrame]
) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame has expected columns and types.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if isinstance(df, pd.DataFrame):
        required_columns = list(SCHEMA_REQUIREMENTS.keys())
        actual_columns = list(df.columns)
        
        missing_columns = set(required_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(required_columns)
        
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
        if extra_columns:
            errors.append(f"Unexpected columns: {extra_columns}")
        
        # Check types (basic)
        for col, requirements in SCHEMA_REQUIREMENTS.items():
            if col in df.columns:
                expected_type = requirements["type"]
                actual_type = df[col].dtype
                
                type_match = False
                if expected_type == "string":
                    type_match = pd.api.types.is_string_dtype(df[col])
                elif expected_type == "integer":
                    type_match = pd.api.types.is_integer_dtype(df[col])
                elif expected_type == "float":
                    type_match = pd.api.types.is_float_dtype(df[col])
                elif expected_type == "date":
                    type_match = pd.api.types.is_datetime64_any_dtype(df[col])
                
                if not type_match:
                    errors.append(f"Column '{col}' has type {actual_type}, expected {expected_type}")
    
    else:
        # PySpark DataFrame
        expected_fields = set(SCHEMA_REQUIREMENTS.keys())
        actual_fields = set(df.columns)
        
        missing_fields = expected_fields - actual_fields
        extra_fields = actual_fields - expected_fields
        
        if missing_fields:
            errors.append(f"Missing fields: {missing_fields}")
        if extra_fields:
            errors.append(f"Unexpected fields: {extra_fields}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def check_nulls(
    df: Union[pd.DataFrame, DataFrame]
) -> Dict[str, int]:
    """
    Check for null values in required columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with column names and null counts
    """
    null_counts = {}
    
    if isinstance(df, pd.DataFrame):
        required_nullable = {
            "review_id": False,
            "source": False,
            "customer_id": False,
            "rating": False,
            "review_text": False,
            "review_date": False,
        }
        
        for col, not_nullable in required_nullable.items():
            if col in df.columns:
                null_count = df[col].isnull().sum()
                null_counts[col] = int(null_count)
                
                if not_nullable and null_count > 0:
                    logger.warning(f"Column '{col}' has {null_count} null values (not allowed)")
    else:
        # PySpark
        for col in df.columns:
            null_count = df.filter(df[col].isNull()).count()
            null_counts[col] = null_count
    
    return null_counts


def check_invalid_ratings(
    df: Union[pd.DataFrame, DataFrame]
) -> Tuple[int, List]:
    """
    Check for ratings outside valid range (1-5).
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (count, list_of_invalid_records)
    """
    invalid_count = 0
    invalid_records = []
    
    if isinstance(df, pd.DataFrame):
        for idx, row in df.iterrows():
            rating = row.get("rating")
            if pd.notna(rating):
                try:
                    rating_int = int(rating)
                    if rating_int < 1 or rating_int > 5:
                        invalid_count += 1
                        invalid_records.append((idx, rating))
                except (ValueError, TypeError):
                    invalid_count += 1
                    invalid_records.append((idx, rating))
    else:
        # PySpark
        invalid_df = df.filter(
            (df.rating < 1) | (df.rating > 5) | (df.rating.isNull())
        )
        invalid_count = invalid_df.count()
        invalid_records = invalid_df.select("review_id", "rating").collect()
    
    return invalid_count, invalid_records


def check_invalid_sources(
    df: Union[pd.DataFrame, DataFrame]
) -> Tuple[int, List]:
    """
    Check for sources not in supported list.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (count, list_of_invalid_sources)
    """
    invalid_count = 0
    invalid_sources = []
    
    if isinstance(df, pd.DataFrame):
        for idx, row in df.iterrows():
            source = row.get("source")
            if pd.notna(source):
                source_str = str(source).strip().lower()
                if source_str not in [s.lower() for s in VALID_SOURCES]:
                    invalid_count += 1
                    invalid_sources.append((idx, source))
    else:
        # PySpark
        valid_sources_lower = [s.lower() for s in VALID_SOURCES]
        invalid_df = df.filter(~df.source.lower().isin(valid_sources_lower))
        invalid_count = invalid_df.count()
        invalid_sources = invalid_df.select("review_id", "source").collect()
    
    return invalid_count, invalid_sources


def check_duplicates(
    df: Union[pd.DataFrame, DataFrame],
    id_column: str = "review_id"
) -> Tuple[int, List]:
    """
    Check for duplicate records by ID.
    
    Args:
        df: Input DataFrame
        id_column: Column to check for duplicates
        
    Returns:
        Tuple of (count, list_of_duplicate_ids)
    """
    duplicate_count = 0
    duplicate_ids = []
    
    if isinstance(df, pd.DataFrame):
        duplicates = df[df.duplicated(subset=[id_column], keep=False)]
        duplicate_count = len(duplicates)
        duplicate_ids = duplicates[id_column].tolist()
    else:
        # PySpark
        duplicates = df.groupBy(id_column).count().filter("count > 1")
        duplicate_count = duplicates.count()
        duplicate_ids = [row[id_column] for row in duplicates.collect()]
    
    logger.info(f"Found {duplicate_count} duplicate records by {id_column}")
    return duplicate_count, duplicate_ids


def check_empty_text(
    df: Union[pd.DataFrame, DataFrame],
    text_column: str = "review_text"
) -> Tuple[int, List]:
    """
    Check for empty or whitespace-only text.
    
    Args:
        df: Input DataFrame
        text_column: Column containing text
        
    Returns:
        Tuple of (count, list_of_invalid_records)
    """
    empty_count = 0
    empty_records = []
    
    if isinstance(df, pd.DataFrame):
        for idx, row in df.iterrows():
            text = row.get(text_column)
            if pd.isna(text) or str(text).strip() == "":
                empty_count += 1
                empty_records.append((idx, text))
    else:
        # PySpark
        empty_df = df.filter(
            df[text_column].isNull() | (df[text_column] == "") | (df[text_column].startswith(" ") & df[text_column].endswith(" "))
        )
        empty_count = empty_df.count()
        empty_records = empty_df.select("review_id", text_column).collect()
    
    return empty_count, empty_records


def run_all_validations(
    df: Union[pd.DataFrame, DataFrame]
) -> Dict:
    """
    Run all validations and return summary.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "total_records": len(df) if isinstance(df, pd.DataFrame) else df.count(),
        "timestamp": str(pd.Timestamp.now()),
        "validations": {}
    }
    
    # Run each validation
    is_valid_schema, schema_errors = validate_schema(df)
    results["validations"]["schema"] = {
        "is_valid": is_valid_schema,
        "errors": schema_errors
    }
    
    null_counts = check_nulls(df)
    results["validations"]["nulls"] = null_counts
    
    invalid_rating_count, _ = check_invalid_ratings(df)
    results["validations"]["invalid_ratings"] = invalid_rating_count
    
    invalid_source_count, _ = check_invalid_sources(df)
    results["validations"]["invalid_sources"] = invalid_source_count
    
    duplicate_count, _ = check_duplicates(df)
    results["validations"]["duplicate_records"] = duplicate_count
    
    empty_text_count, _ = check_empty_text(df)
    results["validations"]["empty_text"] = empty_text_count
    
    # Calculate summary
    is_all_valid = (
        is_valid_schema and
        invalid_rating_count == 0 and
        invalid_source_count == 0 and
        duplicate_count == 0 and
        empty_text_count == 0
    )
    results["is_valid"] = is_all_valid
    
    return results


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m data_quality.checks <csv_file_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    print(f"Running data quality checks on: {csv_path}")
    
    # Read data
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records\n")
    
    # Run validations
    results = run_all_validations(df)
    
    # Print summary
    print("=" * 60)
    print("DATA QUALITY SUMMARY")
    print("=" * 60)
    print(f"Total Records: {results['total_records']}")
    print(f"Overall Valid: {results['is_valid']}")
    print()
    
    for validation_name, result in results["validations"].items():
        if validation_name == "schema":
            print(f"Schema Validation:")
            print(f"  Is Valid: {result['is_valid']}")
            if result['errors']:
                print(f"  Errors: {result['errors']}")
        elif validation_name == "nulls":
            print(f"Null Checks:")
            for col, count in result.items():
                print(f"  {col}: {count} nulls")
        else:
            print(f"{validation_name.replace('_', ' ').title()}: {result}")
    
    print("=" * 60)
