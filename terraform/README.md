# GCP Infrastructure as Code

This directory contains Terraform configuration to provision GCP resources.

## Resources

- Google Cloud Storage buckets (RAW, TRUSTED, CURATED)
- BigQuery dataset
- BigQuery tables
- IAM roles and permissions

## Prerequisites

1. Install Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli
2. Authenticate with GCP:
   ```bash
   gcloud auth application-default login
   ```

## Usage

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan -var="project_id=your-project-id"

# Apply changes
terraform apply -var="project_id=your-project-id"

# Destroy resources
terraform destroy -var="project_id=your-project-id"
```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | GCP Project ID | *Required* |
| `region` | GCP Region | `us-central1` |

## Outputs

| Output | Description |
|--------|-------------|
| `raw_bucket` | RAW bucket name |
| `trusted_bucket` | TRUSTED bucket name |
| `curated_bucket` | CURATED bucket name |
| `dataset_id` | BigQuery dataset ID |
