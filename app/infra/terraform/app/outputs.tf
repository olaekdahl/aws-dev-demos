output "site_url" {
  value       = "https://${var.domain_name}"
  description = "Public website URL."
}

output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "ALB DNS name."
}

output "ecr_api_repo_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_worker_repo_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "ecr_web_repo_url" {
  value = aws_ecr_repository.web.repository_url
}

output "dynamodb_tables" {
  value = {
    quizzes  = aws_dynamodb_table.quizzes.name
    attempts = aws_dynamodb_table.attempts.name
    exports  = aws_dynamodb_table.exports.name
  }
}

output "s3_exports_bucket" {
  value = aws_s3_bucket.exports.bucket
}

output "s3_alb_logs_bucket" {
  value       = aws_s3_bucket.alb_logs.bucket
  description = "S3 bucket receiving ALB access logs."
}

output "sqs_jobs_queue_url" {
  value = aws_sqs_queue.jobs.url
}

output "github_actions_role_arn" {
  value       = try(aws_iam_role.github_actions[0].arn, null)
  description = "IAM role that GitHub Actions can assume via OIDC (if github_repo was set)."
}

output "cloudwatch_dashboard_name" {
  value       = aws_cloudwatch_dashboard.main.dashboard_name
  description = "CloudWatch dashboard name."
}

output "cloudwatch_dashboard_url" {
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
  description = "Convenience link to the dashboard in the AWS Console."
}

# -----------------------------------------------------------------------------
# Cognito outputs
# -----------------------------------------------------------------------------

output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.main.id
  description = "Cognito User Pool ID."
}

output "cognito_user_pool_client_id" {
  value       = aws_cognito_user_pool_client.web.id
  description = "Cognito User Pool Client ID for the web app."
}

output "cognito_region" {
  value       = var.aws_region
  description = "AWS region where Cognito is deployed."
}
