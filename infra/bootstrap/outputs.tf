output "state_bucket_name" {
  value       = aws_s3_bucket.state.bucket
  description = "S3 bucket to use as the Terraform backend."
}

output "state_bucket_arn" {
  value       = aws_s3_bucket.state.arn
  description = "S3 bucket ARN for exact IAM resource references."
}

output "state_kms_key_arn" {
  value       = aws_kms_key.state.arn
  description = "KMS key ARN used for state encryption."
}
