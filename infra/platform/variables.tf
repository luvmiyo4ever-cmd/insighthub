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

variable "github_plan_environment" {
  type    = string
  default = "aws-plan"
}

variable "github_apply_environment" {
  type    = string
  default = "aws-apply"
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

variable "rds_skip_final_snapshot" {
  type    = bool
  default = false
}

variable "rds_secret_kms_key_id" {
  type     = string
  nullable = true
  default  = null
}

variable "rds_log_kms_key_id" {
  type        = string
  description = "Existing customer-managed KMS key ARN for RDS logs and Performance Insights."

  validation {
    condition     = can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.rds_log_kms_key_id))
    error_message = "Use an explicit existing customer-managed KMS key ARN."
  }
}

variable "rds_log_retention_days" {
  type        = number
  default     = 1
  description = "Short-lab CloudWatch PostgreSQL log retention."

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.rds_log_retention_days)
    error_message = "Use a CloudWatch Logs-supported retention period."
  }
}

variable "app_secret_rotation_lambda_arn" {
  type        = string
  description = "Existing reviewed Lambda ARN that implements this app secret's provider-specific rotation contract."

  validation {
    condition     = can(regex("^arn:[^:]+:lambda:[^:]+:[0-9]{12}:function:.+$", var.app_secret_rotation_lambda_arn))
    error_message = "Use an explicit existing rotation Lambda ARN."
  }
}

variable "app_secret_rotation_days" {
  type        = number
  default     = 30
  description = "Approved automatic rotation cadence for the app secret."

  validation {
    condition     = var.app_secret_rotation_days >= 1 && var.app_secret_rotation_days <= 365
    error_message = "Use a rotation cadence between 1 and 365 days."
  }
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

variable "redis_kms_key_id" {
  type        = string
  description = "Existing customer-managed KMS key ARN for ElastiCache encryption at rest."

  validation {
    condition     = can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.redis_kms_key_id))
    error_message = "Use an explicit existing customer-managed KMS key ARN."
  }
}

variable "redis_auth_token" {
  type        = string
  sensitive   = true
  description = "Protected ElastiCache AUTH token; supply only through a protected secret, never source or example tfvars."

  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128 && can(regex("^[A-Za-z0-9!&#$^<>-]+$", var.redis_auth_token))
    error_message = "Redis AUTH token must be 16-128 characters using ElastiCache-supported characters."
  }
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
