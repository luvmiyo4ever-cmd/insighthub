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

variable "state_access_log_bucket_name" {
  type        = string
  description = "Existing dedicated S3 bucket that accepts server-access logs for the state bucket."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{2,62}$", var.state_access_log_bucket_name))
    error_message = "Use the exact existing access-log bucket name."
  }
}

variable "state_replica_bucket_arn" {
  type        = string
  description = "Existing versioned S3 bucket ARN in the approved replica region."

  validation {
    condition     = can(regex("^arn:[^:]+:s3:::[a-z0-9][a-z0-9.-]{2,62}$", var.state_replica_bucket_arn))
    error_message = "Use an exact existing S3 bucket ARN for cross-region replication."
  }
}

variable "state_replica_kms_key_arn" {
  type        = string
  description = "Existing customer-managed KMS key ARN in the replica bucket's region."

  validation {
    condition     = can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.state_replica_kms_key_arn))
    error_message = "Use an exact existing replica-region KMS key ARN."
  }
}
