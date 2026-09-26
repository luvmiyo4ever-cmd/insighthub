locals {
  tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = var.managed_by
    LabId       = var.lab_id
    ExpiresAt   = var.expires_at
  }
}
