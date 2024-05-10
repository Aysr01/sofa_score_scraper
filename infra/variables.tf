variable "credentials_location" {
  description = "The location of the GCP credentials file"
  type = string
}

variable "project_id" {
  description = "The GCP project ID"
  type = string
}

variable "region" {
  description = "The GCP region"
  type = string
}

variable "schema_file" {
  description = "The location of the BigQuery schema file"
  type = string
}