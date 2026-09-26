variable "aws_region" {
  type        = string
  description = "AWS region for the short-lived lab state bucket."
}

variable "project" {
  type        = string
  description = "Project identifier used in names and tags."
}

variable "environment" {
  type        = string
  description = "Environment identifier, for example lab."
}

variable "owner" {
  type        = string
  description = "Human owner of the lab resources."
}

variable "cost_center" {
  type        = string
  description = "Cost attribution label."
}

variable "lab_id" {
  type        = string
  description = "Unique lab identifier."
}

variable "expires_at" {
  type        = string
  description = "Planned teardown timestamp in ISO-8601 format."
}

variable "state_bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name for Terraform state."
}
