# GCP Provider

provider "google" {
    credentials = file(var.credentials_location)
    project = var.project_id
    region = var.region
}