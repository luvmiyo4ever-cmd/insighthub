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

data "aws_partition" "current" {}

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
  # These AWS read APIs do not support resource-level permissions. Keep their
  # list explicit and limit calls to the reviewed provider region.
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeRouteTables",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeTags",
      "ec2:DescribeVpcs",
      "elasticache:DescribeCacheClusters",
      "elasticache:DescribeCacheParameters",
      "elasticache:DescribeCacheSubnetGroups",
      "elasticache:DescribeEngineDefaultParameters",
      "elasticache:DescribeReplicationGroups",
      "rds:DescribeDBEngineVersions",
      "rds:DescribeDBInstances",
      "rds:DescribeDBSubnetGroups"
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "iam:GetOpenIDConnectProvider",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies"
    ]
    resources = [
      aws_iam_openid_connect_provider.eks.arn,
      aws_iam_openid_connect_provider.github.arn,
      aws_iam_role.github_plan.arn,
      aws_iam_role.github_apply.arn,
      aws_iam_role.api_irsa.arn,
      aws_iam_role.worker_irsa.arn,
      aws_iam_role.rds_monitoring.arn
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:DescribeSecret"]
    resources = concat([aws_secretsmanager_secret.app.arn], var.provider_secret_arns)
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

resource "aws_lambda_permission" "app_secret_rotation" {
  statement_id  = "AllowSecretsManagerRotation"
  action        = "lambda:InvokeFunction"
  function_name = var.app_secret_rotation_lambda_arn
  principal     = "secretsmanager.amazonaws.com"
  source_arn    = aws_secretsmanager_secret.app.arn
}

resource "aws_secretsmanager_secret_rotation" "app" {
  secret_id           = aws_secretsmanager_secret.app.id
  rotation_lambda_arn = var.app_secret_rotation_lambda_arn

  rotation_rules {
    automatically_after_days = var.app_secret_rotation_days
  }

  depends_on = [aws_lambda_permission.app_secret_rotation]
}

data "aws_iam_policy_document" "rds_monitoring_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name               = "${var.project}-${var.environment}-rds-monitoring"
  assume_role_policy = data.aws_iam_policy_document.rds_monitoring_trust.json
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
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

resource "aws_cloudwatch_log_group" "postgres" {
  for_each = toset(["postgresql", "upgrade"])

  name              = "/aws/rds/instance/${var.project}-${var.environment}-postgres/${each.value}"
  kms_key_id        = var.rds_log_kms_key_id
  retention_in_days = var.rds_log_retention_days
}

resource "aws_db_parameter_group" "postgres" {
  name        = "${var.project}-${var.environment}-postgres"
  family      = "postgres16"
  description = "InsightHub PostgreSQL logging parameters"

  # DDL captures schema migration activity without logging document DML.
  parameter {
    name         = "log_statement"
    value        = "ddl"
    apply_method = "immediate"
  }

  parameter {
    name         = "rds.log_retention_period"
    value        = tostring(var.rds_instance_log_retention_minutes)
    apply_method = "immediate"
  }

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "immediate"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                            = "${var.project}-${var.environment}-postgres"
  engine                                = "postgres"
  engine_version                        = var.rds_engine_version
  instance_class                        = var.rds_instance_class
  allocated_storage                     = var.rds_storage_gb
  storage_type                          = "gp3"
  storage_encrypted                     = true
  kms_key_id                            = var.rds_secret_kms_key_id
  db_name                               = var.rds_database_name
  username                              = var.rds_master_username
  manage_master_user_password           = true
  master_user_secret_kms_key_id         = var.rds_secret_kms_key_id
  port                                  = 5432
  publicly_accessible                   = false
  multi_az                              = true
  deletion_protection                   = true
  iam_database_authentication_enabled   = true
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_kms_key_id       = var.rds_log_kms_key_id
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn
  auto_minor_version_upgrade            = true
  skip_final_snapshot                   = var.rds_skip_final_snapshot
  final_snapshot_identifier             = var.rds_skip_final_snapshot ? null : "${var.project}-${var.environment}-postgres-final"
  backup_retention_period               = var.rds_backup_retention_days
  db_subnet_group_name                  = aws_db_subnet_group.postgres.name
  parameter_group_name                  = aws_db_parameter_group.postgres.name
  vpc_security_group_ids                = [aws_security_group.data.id]
  copy_tags_to_snapshot                 = true

  depends_on = [aws_cloudwatch_log_group.postgres]
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
  num_cache_clusters         = 2
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.data.id]
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  kms_key_id                 = var.redis_kms_key_id
  auth_token                 = var.redis_auth_token
  auth_token_update_strategy = "SET"
  automatic_failover_enabled = true
  multi_az_enabled           = true
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
