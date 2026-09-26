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

resource "aws_s3_bucket_logging" "state" {
  bucket        = aws_s3_bucket.state.id
  target_bucket = var.state_access_log_bucket_name
  target_prefix = "insighthub-state/"

  target_object_key_format {
    partitioned_prefix {
      partition_date_source = "EventTime"
    }
  }
}

resource "aws_s3_bucket_notification" "state" {
  bucket      = aws_s3_bucket.state.id
  eventbridge = true
}

data "aws_iam_policy_document" "state_replication_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "state_replication" {
  name               = "${var.project}-${var.environment}-state-replication"
  assume_role_policy = data.aws_iam_policy_document.state_replication_trust.json
}

data "aws_iam_policy_document" "state_replication_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket"
    ]
    resources = [aws_s3_bucket.state.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectVersionTagging"
    ]
    resources = ["${aws_s3_bucket.state.arn}/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:ReplicateDelete",
      "s3:ReplicateObject",
      "s3:ReplicateTags"
    ]
    resources = ["${var.state_replica_bucket_arn}/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey"
    ]
    resources = [aws_kms_key.state.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:GenerateDataKey"
    ]
    resources = [var.state_replica_kms_key_arn]
  }
}

resource "aws_iam_role_policy" "state_replication" {
  name   = "${var.project}-${var.environment}-state-replication"
  role   = aws_iam_role.state_replication.id
  policy = data.aws_iam_policy_document.state_replication_permissions.json
}

resource "aws_s3_bucket_replication_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  role   = aws_iam_role.state_replication.arn

  rule {
    id       = "cross-region-state-replication"
    priority = 1
    status   = "Enabled"

    filter {}

    delete_marker_replication {
      status = "Disabled"
    }

    destination {
      bucket        = var.state_replica_bucket_arn
      storage_class = "STANDARD"

      encryption_configuration {
        replica_kms_key_id = var.state_replica_kms_key_arn
      }
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.state]
}
