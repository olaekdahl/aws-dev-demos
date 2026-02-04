resource "aws_rds_cluster" "aurora" {
  cluster_identifier      = "capstone-aurora"
  engine                  = var.db_engine # "aurora-mysql" or "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = var.db_engine_version
  database_name           = var.db_name
  master_username         = var.db_username
  master_password         = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.aurora.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  backup_retention_period = 3
  preferred_backup_window = "07:00-09:00"
  skip_final_snapshot     = true
}

# Writer in AZ 0
resource "aws_rds_cluster_instance" "writer" {
  identifier          = "capstone-aurora-writer"
  cluster_identifier  = aws_rds_cluster.aurora.id
  instance_class      = var.db_instance_class
  engine              = var.db_engine
  engine_version      = var.db_engine_version
  publicly_accessible = false
}

# Reader in AZ 1
resource "aws_rds_cluster_instance" "reader" {
  identifier          = "capstone-aurora-reader"
  cluster_identifier  = aws_rds_cluster.aurora.id
  instance_class      = var.db_instance_class
  engine              = var.db_engine
  engine_version      = var.db_engine_version
  publicly_accessible = false
}