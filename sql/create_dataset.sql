-- Create customer_experience BigQuery dataset

CREATE SCHEMA IF NOT EXISTS customer_experience
OPTIONS(
  description = "Dataset for customer experience analysis",
  location = "US"
);
