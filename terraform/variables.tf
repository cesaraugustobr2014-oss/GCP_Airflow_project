# Variables for Customer Experience Data Pipeline

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "buckets" {
  description = "GCS bucket names"
  type = object({
    raw     = string
    trusted = string
    curated = string
  })
  default = {
    raw     = "customer-experience-raw"
    trusted = "customer-experience-trusted"
    curated = "customer-experience-curated"
  }
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "customer_experience"
}
