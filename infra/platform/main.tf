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

locals {
  eks_oidc_hostpath = replace(var.eks_oidc_issuer, "https://", "")
}

data "tls_certificate" "eks_oidc" {
  url = var.eks_oidc_issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = var.eks_oidc_issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc.certificates[0].sha1_fingerprint]
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [var.github_oidc_thumbprint]
}

data "aws_iam_policy_document" "github_plan_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:environment:${var.github_plan_environment}"]
    }
  }
}

data "aws_iam_policy_document" "github_apply_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:environment:${var.github_apply_environment}"]
    }
  }
}

resource "aws_iam_role" "github_plan" {
  name               = "${var.project}-${var.environment}-github-plan"
  assume_role_policy = data.aws_iam_policy_document.github_plan_trust.json
}

data "aws_iam_policy_document" "github_plan_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "eks:Describe*",
      "eks:List*",
      "iam:Get*",
      "iam:List*",
      "rds:Describe*",
      "elasticache:Describe*",
      "secretsmanager:DescribeSecret"
    ]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [var.state_bucket_arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = [var.state_object_arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [var.state_lock_object_arn]
  }
}

resource "aws_iam_role_policy" "github_plan" {
  name   = "${var.project}-${var.environment}-github-plan"
  role   = aws_iam_role.github_plan.id
  policy = data.aws_iam_policy_document.github_plan_permissions.json
}

resource "aws_iam_role" "github_apply" {
  name               = "${var.project}-${var.environment}-github-apply"
  assume_role_policy = data.aws_iam_policy_document.github_apply_trust.json
}

resource "aws_iam_role_policy" "github_apply" {
  name   = "${var.project}-${var.environment}-github-apply"
  role   = aws_iam_role.github_apply.id
  policy = var.apply_policy_json
}

data "aws_iam_policy_document" "irsa_secret_read" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"]
    resources = var.provider_secret_arns
  }
}

data "aws_iam_policy_document" "api_irsa_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_hostpath}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_hostpath}:sub"
      values   = ["system:serviceaccount:${var.kubernetes_namespace}:${var.api_service_account_name}"]
    }
  }
}

data "aws_iam_policy_document" "worker_irsa_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_hostpath}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_hostpath}:sub"
      values   = ["system:serviceaccount:${var.kubernetes_namespace}:${var.worker_service_account_name}"]
    }
  }
}

resource "aws_iam_role" "api_irsa" {
  name               = "${var.project}-${var.environment}-api-irsa"
  assume_role_policy = data.aws_iam_policy_document.api_irsa_trust.json
}

resource "aws_iam_role_policy" "api_irsa_secrets" {
  name   = "${var.project}-${var.environment}-api-secrets"
  role   = aws_iam_role.api_irsa.id
  policy = data.aws_iam_policy_document.irsa_secret_read.json
}

resource "aws_iam_role" "worker_irsa" {
  name               = "${var.project}-${var.environment}-worker-irsa"
  assume_role_policy = data.aws_iam_policy_document.worker_irsa_trust.json
}

resource "aws_iam_role_policy" "worker_irsa_secrets" {
  name   = "${var.project}-${var.environment}-worker-secrets"
  role   = aws_iam_role.worker_irsa.id
  policy = data.aws_iam_policy_document.irsa_secret_read.json
}

resource "aws_secretsmanager_secret" "app" {
  name                    = var.secret_name
  kms_key_id              = var.secret_kms_key_id
  recovery_window_in_days = 7
}

resource "aws_security_group" "data" {
  name                   = "${var.project}-${var.environment}-data"
  description            = "Private PostgreSQL and Redis access from EKS nodes only"
  vpc_id                 = var.vpc_id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "postgres" {
  security_group_id            = aws_security_group.data.id
  referenced_security_group_id = var.eks_node_security_group_id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  description                  = "PostgreSQL from EKS nodes only"
}

resource "aws_vpc_security_group_ingress_rule" "redis" {
  security_group_id            = aws_security_group.data.id
  referenced_security_group_id = var.eks_node_security_group_id
  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
  description                  = "Redis from EKS nodes only"
}

resource "aws_vpc_security_group_egress_rule" "data" {
  security_group_id = aws_security_group.data.id
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "-1"
  description       = "Egress within the VPC CIDR"
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project}-${var.environment}-postgres"
  subnet_ids = var.private_subnet_ids
}

resource "aws_db_instance" "postgres" {
  identifier                    = "${var.project}-${var.environment}-postgres"
  engine                        = "postgres"
  engine_version                = var.rds_engine_version
  instance_class                = var.rds_instance_class
  allocated_storage             = var.rds_storage_gb
  storage_type                  = "gp3"
  storage_encrypted             = true
  kms_key_id                    = var.rds_secret_kms_key_id
  db_name                       = var.rds_database_name
  username                      = var.rds_master_username
  manage_master_user_password   = true
  master_user_secret_kms_key_id = var.rds_secret_kms_key_id
  port                          = 5432
  publicly_accessible           = false
  multi_az                      = false
  deletion_protection           = var.rds_deletion_protection
  auto_minor_version_upgrade    = true
  skip_final_snapshot           = var.rds_skip_final_snapshot
  final_snapshot_identifier     = var.rds_skip_final_snapshot ? null : "${var.project}-${var.environment}-postgres-final"
  backup_retention_period       = var.rds_backup_retention_days
  db_subnet_group_name          = aws_db_subnet_group.postgres.name
  vpc_security_group_ids        = [aws_security_group.data.id]
  copy_tags_to_snapshot         = true
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project}-${var.environment}-redis"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project}-${var.environment}-redis"
  description                = "Private Redis queue for InsightHub"
  engine                     = "redis"
  engine_version             = var.redis_engine_version
  node_type                  = var.redis_node_type
  num_cache_clusters         = var.redis_num_cache_clusters
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.data.id]
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  auto_minor_version_upgrade = true
  apply_immediately          = true
}

resource "kubernetes_namespace_v1" "insighthub" {
  metadata {
    name   = var.kubernetes_namespace
    labels = module.standard_tags.tags
  }
}

resource "kubernetes_service_account_v1" "api" {
  metadata {
    name        = var.api_service_account_name
    namespace   = kubernetes_namespace_v1.insighthub.metadata[0].name
    labels      = module.standard_tags.tags
    annotations = { "eks.amazonaws.com/role-arn" = aws_iam_role.api_irsa.arn }
  }
}

resource "kubernetes_service_account_v1" "worker" {
  metadata {
    name        = var.worker_service_account_name
    namespace   = kubernetes_namespace_v1.insighthub.metadata[0].name
    labels      = module.standard_tags.tags
    annotations = { "eks.amazonaws.com/role-arn" = aws_iam_role.worker_irsa.arn }
  }
}
