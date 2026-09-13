# Google Cloud Storage buckets for Data Lake

# RAW layer bucket
resource "google_storage_bucket" "raw" {
  name     = var.buckets.raw
  location = var.region

  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365 # Delete after 1 year
    }
  }
}

# TRUSTED layer bucket
resource "google_storage_bucket" "trusted" {
  name     = var.buckets.trusted
  location = var.region

  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365 # Delete after 1 year
    }
  }
}

# CURATED layer bucket
resource "google_storage_bucket" "curated" {
  name     = var.buckets.curated
  location = var.region

  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365 # Delete after 1 year
    }
  }
}
