-- Create dimension and fact tables for customer experience analysis

-- Dimension: Source
CREATE TABLE IF NOT EXISTS customer_experience.dim_source (
  source_id INT64 OPTIONS(description="Unique source identifier"),
  source_name STRING OPTIONS(description="Source name (google_reviews, tripadvisor, yelp, email, social_media)")
)
CLUSTER BY source_id;

-- Dimension: Location
CREATE TABLE IF NOT EXISTS customer_experience.dim_location (
  location_id INT64 OPTIONS(description="Unique location identifier"),
  city STRING OPTIONS(description="City name"),
  state STRING OPTIONS(description="State abbreviation"),
  country STRING OPTIONS(description="Country code (BR)")
)
CLUSTER BY country, state;

-- Fact Table: Reviews
CREATE TABLE IF NOT EXISTS customer_experience.fact_reviews (
  review_id STRING OPTIONS(description="Unique review identifier"),
  customer_id STRING OPTIONS(description="Customer identifier"),
  source_id INT64 OPTIONS(description="Foreign key to dim_source"),
  location_id INT64 OPTIONS(description="Foreign key to dim_location"),
  rating INT64 OPTIONS(description="Rating (1-5)"),
  review_text STRING OPTIONS(description="Cleaned review text"),
  sentiment STRING OPTIONS(description="Sentiment classification (POSITIVE/NEUTRAL/NEGATIVE)"),
  sentiment_score FLOAT64 OPTIONS(description="Sentiment score (-1.0 to +1.0)"),
  review_date DATE OPTIONS(description="Date of the review"),
  ingestion_timestamp TIMESTAMP OPTIONS(description="When record was ingested"),
  processing_timestamp TIMESTAMP OPTIONS(description="When record was processed")
)
PARTITION BY review_date
CLUSTER BY source_id, location_id, sentiment;

-- Comments for documentation
COMMENT ON TABLE customer_experience.fact_reviews IS 'Main fact table containing customer reviews with sentiment analysis';
COMMENT ON COLUMN customer_experience.fact_reviews.sentiment IS 'POSITIVE (score >= 0.5), NEUTRAL (-0.5 < score < 0.5), NEGATIVE (score <= -0.5)';
