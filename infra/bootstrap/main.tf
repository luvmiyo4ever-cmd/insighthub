module "standard_tags" {
  source = "../modules/standard-tags"

  project     = var.project
  environment = var.environment
  owner       = var.owner
  cost_center = var.cost_center
  managed_by  = "terraform"
  lab_id      = var.lab_id
  expires_at  = var.expires_at
}

data "aws_caller_identity" "current" {}

resource "aws_kms_key" "state" {
  description             = "Terraform state encryption key for ${var.project}-${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "state" {
  name          = "alias/${var.project}-${var.environment}-terraform-state"
  target_key_id = aws_kms_key.state.key_id
}

resource "aws_kms_key_policy" "state" {
  key_id = aws_kms_key.state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "EnableAccountAdministration"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }
      Action   = "kms:*"
      Resource = "*"
    }]
  })
}

resource "aws_s3_bucket" "state" {
  bucket        = var.state_bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_ownership_controls" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    id     = "retain-state-history-for-lab-recovery"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.state.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_policy" "state_tls_only" {
  bucket = aws_s3_bucket.state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.state.arn,
        "${aws_s3_bucket.state.arn}/*"
      ]
      Condition = {
        Bool = {
          "aws:SecureTransport" = "false"
        }
      }
    }]
  })
}
