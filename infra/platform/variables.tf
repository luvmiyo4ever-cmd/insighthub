variable "aws_region" {
  type = string
}

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type = string
}

variable "lab_id" {
  type = string
}

variable "expires_at" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "eks_oidc_issuer" {
  type = string
}

variable "eks_node_security_group_id" {
  type = string
}

variable "kubernetes_host" {
  type = string
}

variable "kubernetes_ca_certificate" {
  type      = string
  sensitive = true
}

variable "kubernetes_token" {
  type      = string
  sensitive = true
}

variable "kubernetes_namespace" {
  type    = string
  default = "insighthub"
}

variable "api_service_account_name" {
  type    = string
  default = "insighthub-api"
}

variable "worker_service_account_name" {
  type    = string
  default = "insighthub-worker"
}

variable "github_repository" {
  type = string

  validation {
    condition     = can(regex("^[^/]+/[^/]+$", var.github_repository))
    error_message = "Use the exact GitHub owner/repository form."
  }
}

variable "github_apply_branch" {
  type    = string
  default = "main"
}

variable "github_oidc_thumbprint" {
  type = string

  validation {
    condition     = can(regex("^[0-9a-fA-F]{40}$", var.github_oidc_thumbprint))
    error_message = "Use the reviewed 40-character GitHub OIDC CA thumbprint."
  }
}

variable "state_bucket_arn" {
  type = string
}

variable "state_object_arn" {
  type = string
}

variable "state_lock_object_arn" {
  type = string
}

variable "provider_secret_arns" {
  type = list(string)

  validation {
    condition     = length(var.provider_secret_arns) > 0 && alltrue([for arn in var.provider_secret_arns : !strcontains(arn, "*")])
    error_message = "Secret ARNs must be explicit and cannot contain wildcards."
  }
}

variable "rds_engine_version" {
  type = string

  validation {
    condition     = startswith(var.rds_engine_version, "16.")
    error_message = "Review and supply an exact PostgreSQL 16.x engine version."
  }
}

variable "rds_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "rds_master_username" {
  type = string
}

variable "rds_database_name" {
  type    = string
  default = "insighthub"
}

variable "rds_storage_gb" {
  type    = number
  default = 20
}

variable "rds_backup_retention_days" {
  type    = number
  default = 1
}

variable "rds_deletion_protection" {
  type    = bool
  default = false
}

variable "rds_skip_final_snapshot" {
  type    = bool
  default = false
}

variable "rds_secret_kms_key_id" {
  type     = string
  nullable = true
  default  = null
}

variable "redis_engine_version" {
  type = string

  validation {
    condition     = startswith(var.redis_engine_version, "7.")
    error_message = "Review and supply an exact Redis 7.x engine version."
  }
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "redis_num_cache_clusters" {
  type    = number
  default = 1
}

variable "secret_name" {
  type = string
}

variable "secret_kms_key_id" {
  type     = string
  nullable = true
  default  = null
}

variable "apply_policy_json" {
  type        = string
  description = "Human-reviewed exact policy for the apply role; never put credentials here."

  validation {
    condition     = can(jsondecode(var.apply_policy_json)) && !strcontains(var.apply_policy_json, "\"Action\":\"*\"") && !strcontains(var.apply_policy_json, "\"Resource\":\"*\"")
    error_message = "Apply policy must be valid JSON and cannot use exact wildcard Action or Resource values."
  }
}
