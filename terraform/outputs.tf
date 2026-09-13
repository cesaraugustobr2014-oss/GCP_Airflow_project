# Outputs for Customer Experience Data Pipeline

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "raw_bucket" {
  description = "RAW layer GCS bucket"
  value       = google_storage_bucket.raw.name
}

output "trusted_bucket" {
  description = "TRUSTED layer GCS bucket"
  value       = google_storage_bucket.trusted.name
}

output "curated_bucket" {
  description = "CURATED layer GCS bucket"
  value       = google_storage_bucket.curated.name
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_customer_experience.dataset_id
}
