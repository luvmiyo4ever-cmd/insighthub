output "github_plan_role_arn" {
  value = aws_iam_role.github_plan.arn
}

output "github_apply_role_arn" {
  value = aws_iam_role.github_apply.arn
}

output "api_irsa_role_arn" {
  value = aws_iam_role.api_irsa.arn
}

output "worker_irsa_role_arn" {
  value = aws_iam_role.worker_irsa.arn
}

output "app_secret_arn" {
  value = aws_secretsmanager_secret.app.arn
}

output "postgres_endpoint" {
  value = aws_db_instance.postgres.address
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}
