# BigQuery resources

# Dataset
resource "google_bigquery_dataset" "customer_experience" {
  dataset_id = var.dataset_id
  project    = var.project_id
  location   = var.region

  labels = {
    environment = "development"
    project     = "customer-experience"
  }

  access {
    role   = "roles/bigquery.dataViewer"
    user_by_email = "user@example.com" # Replace with actual email
  }
}

# Tables will be created via SQL (see sql/create_tables.sql)
# This allows version control and easier updates
