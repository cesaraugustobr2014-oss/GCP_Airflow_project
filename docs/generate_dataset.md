# Customer Reviews Dataset Generator

Script to generate synthetic customer reviews dataset with intentional data quality issues.

## Usage

```bash
# Generate 10,000 reviews (default)
python scripts/generate_sample_data.py

# Generate custom number of records
python scripts/generate_sample_data.py --num-records 5000

# Custom output path
python scripts/generate_sample_data.py --output-path data/sample/custom_reviews.csv
```

## Output

Generates: `data/sample/reviews.csv`

Fields:
- `review_id`: Unique identifier (REV000001, REV000002, etc.)
- `source`: Review source (google_reviews, tripadvisor, yelp, email, social_media)
- `customer_id`: Customer identifier (CUS001, CUS002, etc.)
- `city`: City name (Brazilian cities)
- `state`: State abbreviation (SP, RJ, MG, etc.)
- `country`: Country code (BR)
- `rating`: Rating (1-5)
- `review_text`: Portuguese review text
- `review_date`: Date of review (format: YYYY-MM-DD)
- `ingestion_timestamp`: Timestamp when record was ingested

## Data Quality Issues

The dataset includes intentional problems to demonstrate data validation and cleaning:

| Issue | Percentage | Description |
|-------|-----------|-------------|
| Duplicates | ~1% | Exact duplicate records |
| Null text | ~0.5% | Missing review text |
| Invalid ratings | ~1% | Ratings outside 1-5 range |
| Missing city | ~0.5% | Missing city information |
| Invalid date | ~0.5% | Invalid date format |
| Extra whitespace | ~2% | Leading/trailing spaces |
| Inconsistent source case | ~1% | Mixed case in source names |
| Incomplete records | ~0.5% | Missing multiple fields |

## Statistics

After generation, the script prints statistics including:
- Total records
- Records by source
- Records by rating
- Count of each data quality issue

## Reproducibility

Uses seed 42 for deterministic output - same data every time.
