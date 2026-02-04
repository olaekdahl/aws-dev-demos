output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}

output "efs_id" {
  value = aws_efs_file_system.shared_efs.id
}

output "aurora_writer_endpoint" {
  value = aws_rds_cluster.aurora.endpoint
}

output "aurora_reader_endpoint" {
  value = aws_rds_cluster.aurora.reader_endpoint
}