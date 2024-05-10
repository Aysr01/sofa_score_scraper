# Purpose: Create a Google Cloud Storage bucket
resource "google_storage_bucket" "football_bucket" {
  name          = "football_bucket"
  location      = "US"
  force_destroy = true
}

# Create a GCP DataSet
resource "google_bigquery_dataset" "football_dataset" {
  dataset_id = "football_dataset"
  project = var.project_id
  location = "US"
}

# Create a GCP Table
resource "google_bigquery_table" "results" {
    table_id = "football_results"
    dataset_id = google_bigquery_dataset.football_dataset.dataset_id
    project = var.project_id
    schema = file(var.schema_file)
}