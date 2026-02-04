resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name}-dashboard"

  dashboard_body = templatefile("${path.module}/dashboard.json.tftpl", {
    region             = var.aws_region
    project            = local.name
    alb_arn_suffix      = aws_lb.this.arn_suffix
    tg_web_arn_suffix   = aws_lb_target_group.web.arn_suffix
    tg_api_arn_suffix   = aws_lb_target_group.api.arn_suffix
    cluster_name        = aws_ecs_cluster.this.name
    api_service_name    = "${local.name}-api"
    web_service_name    = "${local.name}-web"
    worker_service_name = "${local.name}-worker"
    log_group_api       = aws_cloudwatch_log_group.api.name
    log_group_web       = aws_cloudwatch_log_group.web.name
    queue_name          = aws_sqs_queue.jobs.name
    dlq_name            = aws_sqs_queue.jobs_dlq.name
    ddb_quizzes         = aws_dynamodb_table.quizzes.name
    ddb_attempts        = aws_dynamodb_table.attempts.name
    ddb_exports         = aws_dynamodb_table.exports.name
    xray_api_service    = "code-quiz-api"
    xray_worker_service = "code-quiz-worker"
  })

  tags = local.tags
}
