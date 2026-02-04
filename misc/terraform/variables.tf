variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "app_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "db_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.20.0/24", "10.0.21.0/24"]
}

variable "app_desired_capacity" {
  type    = number
  default = 2
}

variable "app_min_size" {
  type    = number
  default = 2
}

variable "app_max_size" {
  type    = number
  default = 4
}

variable "app_instance_type" {
  type    = string
  default = "t3.small"
}

variable "alb_http_port" {
  type    = number
  default = 80
}

variable "db_engine" {
  description = "Aurora engine: aurora-mysql or aurora-postgresql"
  type        = string
  default     = "aurora-mysql"
}

variable "db_engine_version" {
  type = string
  # Example: Aurora MySQL 3 (MySQL 8.0 compatible)
  default = "8.0.mysql_aurora.3.05.2"
}

variable "db_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type    = string
  default = "appuser"
}

variable "db_password" {
  type      = string
  sensitive = true
}